import type { BaseEvent } from "./base";

export interface Representation {
    kind: string;
    type: string;
    id: number;
    complexity: number;
}

export interface CycleReference extends Representation {
    kind: "cycle_reference";
    targetId: number;
}

export interface MaxDepthReached extends Representation {
    kind: "max_depth_reached";
    type: string;
}

export interface UnknownRepresentation extends Representation {
    kind: "unknown";
    type: string;
    value: string;
}

export interface ErrorRepresentation extends Representation {
    kind: "error";
    error_message: string;
    type: string;
    value: string;
}

export interface CompleteFailureRepresentation extends Representation {
    kind: "complete_failure";
    error_message: string;
    new_error_message: string;
}

export interface Primitive extends Representation {
    kind: "primitive";
    value: string;
    type: "str" | "int" | "float" | "bool" | "NoneType";
}

export interface EmptyLinearCollection extends Representation {
    kind: "empty_linear_collection";
    type: "list" | "tuple" | "set" | "frozenset";
}

export interface HomogenousLinearCollection extends Representation {
    kind: "homogenous_linear_collection";
    type: "list" | "set" | "frozenset";
    elementType: string;
    elements: Array<SpecificRepresentation>;
    fullType: string;
}

export interface LinearCollection extends Representation {
    kind: "linear_collection";
    type: "list" | "set" | "frozenset";
    elementType: string;
    elements: Array<SpecificRepresentation>;
    fullType: string;
}

export interface HomogenousGrid extends Representation {
    kind: "homogenous_grid";
    type: "list";
    elementType: string;
    rows: Array<HomogenousLinearCollection>;
    fullType: string;
}

export interface EmptyTuple extends Representation {
    kind: "empty_tuple";
    type: "tuple";
}

export interface TupleRepresentation extends Representation {
    kind: "tuple";
    type: "tuple";
    elements: Array<SpecificRepresentation>;
    fullType: string;
}

export interface ClassInstanceRepresentation extends Representation {
    kind: "class" | "dataclass";
    type: string;
    fields: Array<{
        name: string;
        value: SpecificRepresentation;
    }>;
    fullType: string;
}

export interface UnionRepresentation extends Representation {
    kind: "union";
    type: "union";
    options: Array<SpecificRepresentation>;
    fullType: string;
}

export interface EmptyDict extends Representation {
    kind: "empty_dict";
    type: "dict";
}

export interface Dict extends Representation {
    kind: "dict";
    type: "dict";
    areKeysHomogenous: boolean;
    areValuesHomogenous: boolean;
    keyType: string;
    valueType: string;
    entries: Array<{
        key: SpecificRepresentation;
        value: SpecificRepresentation;
    }>;
    fullType: string;
}

export interface UpdatedStateEvent extends BaseEvent {
    event_type: "UpdatedState";
    representation: SpecificRepresentation;
}

export type SpecificRepresentation =
    | CycleReference
    | MaxDepthReached
    | UnknownRepresentation
    | ErrorRepresentation
    | CompleteFailureRepresentation
    | Primitive
    | EmptyLinearCollection
    | HomogenousLinearCollection
    | LinearCollection
    | HomogenousGrid
    | EmptyTuple
    | TupleRepresentation
    | ClassInstanceRepresentation
    | UnionRepresentation
    | EmptyDict
    | Dict;
