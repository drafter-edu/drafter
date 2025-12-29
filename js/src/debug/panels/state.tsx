export type Table = {
    columns: ["Field", "Type", "Value"] | string[];
    rows: Array<{
        name: string;
        type: string;
        value: string | Table;
    }>;
};

export class StatePanel {
    private currentTable: Table | null = null;
    private fallbackHtml: string = "";

    public renderState(table: Table | null, html?: string): void {
        this.currentTable = table ?? null;
        this.fallbackHtml = html ?? "";

        const section = document.getElementById(
            "drafter-debug-current-state-content"
        );
        if (!section) {
            throw new Error("DebugPanel: State section not found.");
        }

        console.log(table);

        // Render nested tables; else fallback to html
        const renderNestedTable = (tbl: Table): HTMLElement => {
            const tableEl = (
                <table class="drafter-state-table">
                    <thead>
                        <tr>
                            <th>Field</th>
                            <th>Type</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tbl.rows.map((row) => (
                            <tr>
                                <td>{row.name}</td>
                                <td>{row.type}</td>
                                <td>
                                    {typeof row.value === "string" ? (
                                        <pre style="margin:0">{row.value}</pre>
                                    ) : (
                                        renderNestedTable(row.value)
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) as unknown as HTMLElement;
            return tableEl;
        };

        console.log(this.currentTable);

        const result =
            this.currentTable && this.currentTable.rows.length ? (
                renderNestedTable(this.currentTable)
            ) : (
                <div class="state-content">
                    <div
                        dangerouslySetInnerHTML={{ __html: this.fallbackHtml }}
                    ></div>
                </div>
            );

        section.replaceChildren(result);
    }
}
