from workflows.workflow import BaseWorkflow, State


class BaseState(State):
    due_time_warning = 3
    due_time = 4
    max_unassigned_time = 2
    max_unassigned_time_warning = 1


class ReceiveOrderState(BaseState):
    description = 'Initial state'
    name = 'Initial state'
    slug = 'initial_state'
    swimlanes = ['clerk', ]

    def next(self, data, task):
        return [PreparePizzaState, ]


class PreparePizzaState(BaseState):
    description = 'Prepare pizza following the order'
    name = 'Prepare Pizza'
    slug = 'prepare-pizza'
    swimlanes =['cook', ]

    def next(self, data, task):
        return [DeliveryPizzaState, ]


class DeliveryPizzaState(BaseState):
    description = 'Delivery pizza to client'
    is_final = True
    name = 'Delivery Pizza'
    slug = 'delivery-pizza'
    swimlanes = ['delivery', ]


class Workflow(BaseWorkflow):
    description = 'Sell pizza'
    initial_state = ReceiveOrderState
    slug = 'sell-pizza'
    states = [
        ReceiveOrderState,
        PreparePizzaState,
        DeliveryPizzaState,
    ]
