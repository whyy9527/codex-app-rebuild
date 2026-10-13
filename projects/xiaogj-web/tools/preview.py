"""Start the existing local replica for preview; no exploration or source access."""
import argparse
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import build_opener, HTTPCookieProcessor, Request, urlopen
import webbrowser

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
WEB = 'http://127.0.0.1:5183'
API = 'http://127.0.0.1:3101'


def listening(port):
    with socket.socket() as connection:
        connection.settimeout(.3)
        return connection.connect_ex(('127.0.0.1', port)) == 0


def read_url(url):
    with urlopen(url, timeout=3) as response:
        return response.read()


def wait_ready(check, process, seconds=45):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise RuntimeError('服务启动失败；请查看 private/preview/ 下对应日志。')
        try:
            if check():
                return
        except (OSError, URLError, ValueError):
            pass
        time.sleep(.25)
    raise RuntimeError('等待服务就绪超时；请查看 private/preview/ 下对应日志。')


def check_authenticated():
    credentials = json.loads((PROJECT / 'private/local-auth.json').read_text())
    client = build_opener(HTTPCookieProcessor(CookieJar()))
    def post(path, body):
        request = Request(WEB + path, data=json.dumps(body).encode(),
                          headers={'Content-Type': 'application/json', 'Origin': WEB})
        with client.open(request, timeout=10) as response:
            return json.load(response)
    post('/api/auth/login', {key: credentials[key] for key in ('username', 'password')})
    try:
        for path in ('/api/auth/session', '/api/home', '/api/students', '/api/enrollment/defaults',
                     '/api/enrollment/choices/courses', '/api/enrollment/choices/items'):
            with client.open(WEB + path, timeout=10) as response:
                json.load(response)
    finally:
        post('/api/auth/logout', {})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-open', action='store_true', help='不自动打开浏览器')
    parser.add_argument('--check', action='store_true', help='启动并验证登录与业务接口后退出')
    parser.add_argument('--skip-build', action='store_true', help='使用已有构建（默认重新构建）')
    args = parser.parse_args(argv)
    owned = []
    logs = PROJECT / 'private/preview'
    logs.mkdir(parents=True, exist_ok=True)
    def spawn(name, command, cwd=ROOT):
        with (logs / (name + '.log')).open('ab') as stream:
            process = subprocess.Popen(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT,
                                       start_new_session=True)
        owned.append(process)
        return process
    def cleanup():
        for process in reversed(owned):
            # Descendants (npx/pnpm/node) share this owned process group.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for process in reversed(owned):
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
    try:
        required = ['database.env', 'auth.env', 'local-auth.json', 'reference/home-data.json',
                    'reference/enrollment-defaults.json', 'reference/enrollment-choices.json']
        missing = [name for name in required if not (PROJECT / 'private' / name).is_file()]
        if missing or not (PROJECT / 'private/assets').is_dir():
            raise RuntimeError('缺少已授权的本地输入，请按 SETUP.md 准备 private/ 下数据库、账号和素材。')
        npx = shutil.which('npx')
        if not npx:
            raise RuntimeError('需要安装 Node.js/npm，确保 npx 在 PATH 中。')
        pnpm = [npx, '--yes', '--package=node@24.18.0', '--package=pnpm@11.15.1', '--', 'pnpm']
        if not (PROJECT / 'node_modules').is_dir():
            print('安装锁定依赖…', flush=True)
            subprocess.run(pnpm + ['--dir', str(PROJECT), 'install', '--frozen-lockfile'], check=True)
        if not args.skip_build:
            print('构建本地复刻…', flush=True)
            subprocess.run(pnpm + ['--dir', str(PROJECT), 'build'], check=True)
        if not (PROJECT / 'apps/web/dist/index.html').is_file() or not (PROJECT / 'apps/api/dist/main.js').is_file():
            raise RuntimeError('没有可预览的构建，请去掉 --skip-build。')
        if not listening(33084):
            data = PROJECT / 'private/mysql84'
            if not (data / 'auto.cnf').is_file():
                raise RuntimeError('本地 MySQL 尚未初始化，请按 SETUP.md 准备数据库。')
            mysql = os.environ.get('MYSQL84_BIN')
            if not mysql:
                brew = shutil.which('brew')
                if not brew:
                    raise RuntimeError('请设置 MYSQL84_BIN 指向 MySQL 8.4 的 bin 目录。')
                mysql = subprocess.check_output([brew, '--prefix', 'mysql@8.4'], text=True).strip() + '/bin'
            process = spawn('mysql', [str(Path(mysql) / 'mysqld'), '--no-defaults', '--datadir=' + str(data),
                                     '--socket=' + str(PROJECT / 'private/mysql84.sock'),
                                     '--pid-file=' + str(PROJECT / 'private/mysql84.pid'),
                                     '--log-error=' + str(PROJECT / 'private/mysql84.log'),
                                     '--port=33084', '--bind-address=127.0.0.1', '--mysqlx=OFF'])
            wait_ready(lambda: listening(33084), process)
        api_process = None
        if not listening(3101):
            api_process = spawn('api', [npx, '--yes', '--package=node@24.18.0', '--', 'node',
                                        'projects/xiaogj-web/apps/api/dist/main.js'])
        wait_ready(lambda: json.loads(read_url(API + '/api/health')) == {'status': 'ok'}, api_process)
        web_process = None
        if not listening(5183):
            web_process = spawn('web', pnpm + ['--dir', str(PROJECT / 'apps/web'), 'exec', 'vite',
                                               'preview', '--host', '127.0.0.1', '--port', '5183', '--strictPort'])
        wait_ready(lambda: '校管家'.encode() in read_url(WEB), web_process)
        if json.loads(read_url(WEB + '/api/health')) != {'status': 'ok'}:
            raise RuntimeError('预览 API 代理检查失败。')
        check_authenticated()
        print('\n预览已就绪：' + WEB, flush=True)
        print('登录账号见 projects/xiaogj-web/private/local-auth.json（与原版账号不同）。', flush=True)
        if args.check:
            print('登录、首页、学员与报名目录接口检查通过。', flush=True)
            return 0
        if not args.no_open:
            webbrowser.open(WEB)
        print('保持此终端开启；Ctrl+C 关闭本次启动的服务，已有服务保留。', flush=True)
        while True:
            if any(process.poll() is not None for process in owned):
                raise RuntimeError('预览服务已退出，请查看 private/preview/ 下日志。')
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n预览已退出。', flush=True)
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError, HTTPError) as error:
        # Never emit response bodies, credentials, or database connection URLs.
        print('无法启动预览：' + (str(error) if isinstance(error, RuntimeError) else type(error).__name__), flush=True)
        return 1
    finally:
        cleanup()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    raise SystemExit(main())
