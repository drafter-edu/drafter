export { confirmDialog, showDialog } from "./dialogs";
import pkg from "../package.json" with { type: "json" };
import "./components/registry";

export const version = pkg.version;
