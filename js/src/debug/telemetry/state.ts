import type { TelemetryRecord } from "./base";

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
	// The Python describer (_visit_class_instance in
	// src/drafter/data/details/recursive_type_describer.py) does not emit
	// fullType for class/dataclass nodes.
	fullType?: string;
}

export interface UnionRepresentation extends Representation {
	kind: "union";
	type: "union";
	options: Array<SpecificRepresentation>;
	// The Python describer does not yet emit "union" nodes at all (see its
	// roadmap comment), so fullType cannot be relied on.
	fullType?: string;
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

export interface UpdatedStateEvent extends TelemetryRecord {
	kind: "UpdatedState";
	representation: SpecificRepresentation;
}

export interface ImageRepresentation extends Representation {
	kind: "image";
	type: string;
	/**
	 * Preview source: a small thumbnail data URL, the backing URL for an
	 * unloaded URL-backed Picture, or null when no preview is available.
	 */
	value: string | null;
	filename: string | null;
	width: number | null;
	height: number | null;
	mime: string | null;
}

export interface BytesRepresentation extends Representation {
	kind: "bytes";
	type: string;
	length: number;
	/** Short space-separated hex preview of the first bytes. */
	preview: string;
	/** Thumbnail data URL when the bytes are a recognized image. */
	thumbnail: string | null;
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
	| Dict
	| ImageRepresentation
	| BytesRepresentation;
