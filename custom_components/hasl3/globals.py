# pylint: disable=invalid-name, missing-docstring
worker = []

def get_worker():
    if not worker:
        from custom_components.hasl3.haslworker import HaslWorker

        worker.append(HaslWorker())

    return worker[0]
