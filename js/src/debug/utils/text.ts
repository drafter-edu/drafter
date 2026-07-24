export function wordWrap(str: string, maxWidth: number): string {
	const words = str.split(" ");
	let currentLine = "";
	const lines = [];

	for (let i = 0; i < words.length; i++) {
		const word = words[i];

		// Check if adding the next word exceeds the max width
		if ((currentLine + word).length > maxWidth) {
			if (currentLine.trim()) {
				lines.push(currentLine.trim());
			}
			currentLine = word + " ";
		} else {
			currentLine += word + " ";
		}
	}

	// Push the final remaining line
	if (currentLine) {
		lines.push(currentLine.trim());
	}

	return lines.join("\n");
}
