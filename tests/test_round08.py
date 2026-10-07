import unittest
from runtime.components import Context


class ComponentLifecycle(unittest.TestCase):
    def test_dependencies_deactivate_and_reactivate_without_residue(self):
        events = []
        context = Context()
        def dependent(scope):
            events.append('start-b')
            self.assertEqual(scope.require('a'), 42)
            scope.on_close(lambda: events.append('stop-b'))
            return 'b-service'
        def provider(scope):
            events.append('start-a')
            scope.on_close(lambda: events.append('stop-a'))
            return 42
        context.mount('b', dependent, requires=('a',))
        self.assertEqual(context.active(), [])
        context.mount('a', provider)
        self.assertEqual(set(context.active()), {'a', 'b'})
        context.unmount('a')
        self.assertEqual(events, ['start-a', 'start-b', 'stop-b', 'stop-a'])
        self.assertEqual(context.active(), [])
        context.mount('a', provider)
        self.assertEqual(set(context.active()), {'a', 'b'})
        context.close()
        self.assertEqual(context.active(), [])
        context.close()

    def test_start_failure_rolls_back_registered_resources(self):
        events = []
        context = Context()
        def broken(scope):
            scope.on_close(lambda: events.append('cleaned'))
            raise RuntimeError('startup failed')
        with self.assertRaises(RuntimeError):
            context.mount('broken', broken)
        self.assertEqual(events, ['cleaned'])
        self.assertEqual(context.active(), [])
        context.mount('broken', lambda scope: 'recovered')
        context.close()

    def test_cleanup_failures_do_not_skip_other_resources(self):
        events = []
        context = Context()
        def start(scope):
            scope.on_close(lambda: events.append('last'))
            def fail():
                raise RuntimeError('cleanup failed')
            scope.on_close(fail)
            scope.on_close(lambda: events.append('first'))
        context.mount('a', start)
        with self.assertRaises(ExceptionGroup):
            context.close()
        self.assertEqual(events, ['first', 'last'])
        self.assertEqual(context.active(), [])
