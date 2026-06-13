export { confirmDialog, showDialog } from "./dialogs";
import pkg from "../package.json" with { type: "json" };

export const version = pkg.version;
