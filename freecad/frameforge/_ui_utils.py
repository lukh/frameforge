class FormProxy(object):
    def __init__(self, form):
        self.members = {o:f for f in form for o in vars(f)}

    def __getattr__(self, name):
        if name not in self.members:
            raise ValueError(f"{name} not a member of one of the forms")

        return getattr(self.members[name], name)
