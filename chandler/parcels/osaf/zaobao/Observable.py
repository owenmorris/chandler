
class Observable1:
    """mixin class to implement Observable pattern. Used to decouple
    objects, so that changes in one (the observable) can to broadcast to 
    a list of others (observers) in a generic API:
        observer.update(observable, args)
    """
    
    def __init__(self):
        self._v_observers = []
            
    def register(self, observer):
        self._v_observers.append(observer)
        
    def unregister(self, observer):
        self._v_observers.remove(observer)
        
    def broadcast(self,args):
        for observer in self._v_observers:
            observer.update(self,args)