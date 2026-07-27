/**
 * Locale parity checks for the debug UI's newer namespaces.
 *
 * Historically the "es" bundle lagged behind "en" (several button.* keys
 * have no Spanish entry and fall back via fallbackLng). To keep that gap
 * from widening, every key in the namespaces introduced with the tabbed
 * debug panel / header menu bar must exist in BOTH locales, and "es" must
 * never carry keys that "en" lacks.
 */
import { describe, expect, test } from "@jest/globals";

import resources from "../../locales/resources.json";

const en = (resources as Record<string, { common: Record<string, string> }>)
	.en.common;
const es = (resources as Record<string, { common: Record<string, string> }>)
	.es.common;

/** Namespaces that must be fully translated in both locales. */
const PARITY_PREFIXES = [
	"debug.tab",
	"menu.",
	"saveload.",
	"current.",
	"packages.",
	"storage.",
	"runtime.",
	"route_graph.",
	"coverage.",
	"test_wizard.",
	"internals.",
	"viewsource.",
	"state_edit.",
	"footer.status",
	"theme.",
	"time.",
];

function keysInNamespaces(bundle: Record<string, string>): string[] {
	return Object.keys(bundle)
		.filter((key) =>
			PARITY_PREFIXES.some((prefix) => key.startsWith(prefix)),
		)
		.sort();
}

describe("en/es locale parity", () => {
	test("the new debug-UI namespaces are translated in both locales", () => {
		expect(keysInNamespaces(es)).toEqual(keysInNamespaces(en));
	});

	test("es has no keys that en lacks (orphaned translations)", () => {
		const enKeys = new Set(Object.keys(en));
		const orphans = Object.keys(es).filter((key) => !enKeys.has(key));
		expect(orphans).toEqual([]);
	});

	test("no empty translation values in either locale", () => {
		const empties = [
			...Object.entries(en).map(([key, value]) => ["en", key, value]),
			...Object.entries(es).map(([key, value]) => ["es", key, value]),
		].filter(([, , value]) => !String(value).trim());
		expect(empties).toEqual([]);
	});
});
