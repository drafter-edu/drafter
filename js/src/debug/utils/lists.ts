export function intersperse<T>(list: T[], separator: T): T[] {
    if (list.length <= 1) {
        return [...list];
    }

    const result: T[] = [];

    for (let i = 0; i < list.length; i++) {
        result.push(list[i]);

        if (i < list.length - 1) {
            result.push(separator);
        }
    }

    return result;
}
