"""Compare captured login journey facts against fixed observed source evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from capabilities.rebuild.contracts import local_file


def facts(empty, post_login, home):
    return {
        'welcome': '欢迎登录' in empty,
        'username': '请输入带有后缀的用户名，如：张三@xiaogj' in empty,
        'password': '请输入密码' in empty,
        'forgot': bool(re.search(r'\d+ link 忘记密码,', empty)),
        'submit': bool(re.search(r'\d+ link 登录,', empty)),
        'post_login_password_reminder': bool(re.search(r'\d+ heading 修改密码', post_login)),
        'authenticated_home_navigation': all(label in home for label in (
            '招生营销', '前台业务', '教务管理', '人事管理', '进销存管理', '财务管理', '家校服务', '报表中心')),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', default='.')
    parser.add_argument('--book', default='projects/xiaogj-web/auth-scenarios.json')
    parser.add_argument('--observed', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    book = json.loads(local_file(root, args.book).read_text())
    sources = []
    for source in book['reference']:
        path = local_file(root, source['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('Frozen source evidence changed')
        sources.append(path.read_text())
    expected = facts(*sources)
    if not all(expected.values()):
        raise ValueError('Reference evidence does not establish this journey')
    directory = local_file(root, args.observed, must_exist=False)
    actual = facts(*[(directory / name).read_text() for name in ('login-empty.ax.txt', 'post-login.ax.txt', 'after-refresh.ax.txt')])
    checks = [{'id': key, 'source': 'observed', 'status': 'pass' if actual[key] == value else 'fail', 'expected': value, 'actual': actual[key]} for key, value in expected.items()]
    preparation = json.loads((directory / 'preparation.json').read_text())
    if preparation['password_condition'] != 'source-equivalent-weak':
        reminder = next(row for row in checks if row['id'] == 'post_login_password_reminder')
        reminder.update(status='not_run', reason='Source account triggered weak-password policy; independent candidate credentials do not establish the same precondition. Actual absence is retained.')
    result = {'status': 'pass' if all(row['status'] == 'pass' for row in checks) else 'fail', 'checks': checks,
              'not_run': ['login same-state strict frontend', 'promotion layer journey', 'source credential error and recovery semantics', 'Cognito and permission fidelity'],
              'completion': 'not evaluated; this journey and candidate security checks do not establish full product fidelity'}
    with local_file(root, args.out, must_exist=False).open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
