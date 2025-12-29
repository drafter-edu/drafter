function openDb() {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open("fs-handles", 1);
        req.onupgradeneeded = () => req.result.createObjectStore("kv");
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
    });
}

async function idbGet(key: any) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
        const tx = (db as any).transaction("kv", "readonly");
        const store = tx.objectStore("kv");
        const req = store.get(key);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
    });
}

async function idbSet(key: any, value: any) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
        const tx = (db as any).transaction("kv", "readwrite");
        const store = tx.objectStore("kv");
        store.put(value, key);
        tx.oncomplete = () => resolve(value);
        tx.onerror = () => reject(tx.error);
    });
}

export async function mountDirectory(pyodideDirectory: any, directoryKey: any) {
    console.log("Mounting directory with key:", directoryKey);
    let directoryHandle = await idbGet(directoryKey);
    const opts = { id: "mountdirid" };

    if (!directoryHandle) {
        directoryHandle = await window.showDirectoryPicker(opts);
        await idbSet(directoryKey, directoryHandle);
    }

    const permissionStatus = await (directoryHandle as any).requestPermission(
        opts
    );

    if (permissionStatus !== "granted") {
        throw new Error("read access to directory not granted");
    }

    const { syncfs } = await (window as any).pyodide.mountNativeFS(
        pyodideDirectory,
        directoryHandle
    );
    console.log("Mounted directory:", directoryHandle);
    console.log("syncfs function:", syncfs);
    return syncfs;
}
