
AVAILABLE = 0
IN_USE    = 1

views = []
name = "viewpool-%d"
highest = 0

def getView(repo):
    global views, highest

    for i, (view, status) in enumerate(views):
        if status == AVAILABLE:
            views[i] = (view, IN_USE)
            view.cancel( )
            view.refresh( )
            return view

    view = repo.createView(name=name%highest)
    views.append((view, IN_USE))
    highest += 1
    return view

def releaseView(rv):
    global views

    for i, (view, status) in enumerate(views):
        if rv is view:
            views[i] = (view, AVAILABLE)
