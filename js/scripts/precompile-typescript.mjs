import * as fs from "node:fs/promises";
import ts from "typescript"; // CJS module; default import works in ESM

export async function precompileTypeScript(filePath, fileName) {
    const source = await fs.readFile(filePath, "utf8");
    const { outputText, diagnostics, sourceMapText } = ts.transpileModule(
        source,
        {
            compilerOptions: {
                target: ts.ScriptTarget.ES2022,
                module: ts.ModuleKind.ES2022,
                sourceMap: true,
            },
            fileName,
            reportDiagnostics: true,
        }
    );

    if (diagnostics?.length) {
        const formatted = ts.formatDiagnosticsWithColorAndContext(diagnostics, {
            getCurrentDirectory: () => process.cwd(),
            getCanonicalFileName: (f) => f,
            getNewLine: () => "\n",
        });
        console.warn(formatted);
    }

    let code = outputText.trim();

    // Remove trailing `export {};` (with optional semicolon and whitespace/comments)
    code = code.replace(/(?:\r?\n)?export\s*\{\s*\}\s*;?\s*/, "");

    return { code, map: sourceMapText };
}
