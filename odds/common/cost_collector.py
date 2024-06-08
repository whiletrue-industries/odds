class CostCollector():

    def __init__(self, name, costs):
        self.name = name
        self.costs = costs
        self.usage = dict()
        self.transaction_usage = dict()

    def update_cost(self, model, kind, cost):
        for r in [self.usage, self.transaction_usage]:
            r.setdefault(model, {}).setdefault(kind, 0)
            r[model][kind] += cost

    def print_usage(self, usage):
        cost = 0
        msg = f'{self.name} usage:'
        for model, model_usage in usage.items():
            msg += f'\n{model}:'
            for kind, kind_usage in model_usage.items():
                msg += f' {kind}: {kind_usage}'
                cost += kind_usage * self.costs[model][kind]
        if cost:
            msg += f'\n{self.name} cost: $ {cost:.2f}'
            print(msg)

    def start_transaction(self):
        self.transaction_usage = dict()

    def end_transaction(self):
        if self.transaction_usage:
            self.print_usage(self.transaction_usage)
    
    def print_total_usage(self):
        self.print_usage(self.usage)