# http://simpy.readthedocs.io/en/latest/topical_guides/monitoring.html
from functools import wraps
def trace(env, callback):
    """
    Replace the ``step()`` method of *env* with a tracing function
    that calls *callbacks* with an events time, priority, ID and its
    instance just before it is processed.
    """
    def get_wrapper(env_step, callback):
        """Generate the wrapper for env.step()."""
        @wraps(env_step)
        def tracing_step():
            """
            Call *callback* for the next event if one exist before
            calling ``env.step()``.
            """
            if len(env._queue):
                t, prio, eid, event = env._queue[0]
                callback(t, prio, eid, event)
            return env_step()
        return tracing_step

    env.step = get_wrapper(env.step, callback)

