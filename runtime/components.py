"""Small explicit scoped lifecycle, inspired by Cordis; not a Cordis implementation."""


class Scope:
    def __init__(self, context, requires):
        self._context, self._requires, self._cleanup = context, set(requires), []

    def require(self, name):
        if name not in self._requires:
            raise ValueError('dependency must be declared')
        return self._context._services[name][0]

    def on_close(self, callback):
        self._cleanup.append(callback)

    def close(self):
        errors = []
        while self._cleanup:
            try:
                self._cleanup.pop()()
            except Exception as error:
                errors.append(error)
        if errors:
            raise ExceptionGroup('resource cleanup failed', errors)


class Context:
    def __init__(self):
        self._specs, self._services = {}, {}

    def active(self):
        return list(self._services)

    def mount(self, name, start, *, requires=()):
        if name in self._specs or name in requires or not name:
            raise ValueError('duplicate or self-dependent component')
        self._specs[name] = (start, tuple(requires))
        previously_active = set(self._services)
        try:
            self._activate()
        except Exception as error:
            self._specs.pop(name, None)
            try:
                self._stop(set(self._services) - previously_active)
            except Exception as cleanup:
                raise ExceptionGroup("activation and rollback failed", [error, cleanup]) from None
            raise

    def _activate(self):
        changed = True
        while changed:
            changed = False
            for name, (start, requires) in list(self._specs.items()):
                if name not in self._services and all(key in self._services for key in requires):
                    scope = Scope(self, requires)
                    try:
                        service = start(scope)
                    except Exception as error:
                        try:
                            scope.close()
                        except Exception as cleanup:
                            raise ExceptionGroup('startup and cleanup failed', [error, cleanup]) from None
                        raise
                    self._services[name] = (service, scope)
                    changed = True

    def unmount(self, name):
        if name not in self._specs:
            return
        affected = {name}
        while True:
            expanded = affected | {key for key, (_, deps) in self._specs.items() if affected.intersection(deps)}
            if expanded == affected:
                break
            affected = expanded
        self._specs.pop(name)
        self._stop(affected)

    def _stop(self, names):
        errors = []
        for name in reversed(list(self._services)):
            if name in names:
                _, scope = self._services.pop(name)
                try:
                    scope.close()
                except Exception as error:
                    errors.append(error)
        if errors:
            raise ExceptionGroup('component cleanup failed', errors)

    def close(self):
        self._specs.clear()
        self._stop(set(self._services))
