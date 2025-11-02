declare global {
    type pyBool = import("./skulpt").pyBool;
    type pyInt = import("./skulpt").pyInt;
    type pyObject = import("./skulpt").pyObject;
    type pyStr = import("./skulpt").pyStr;
    type pyList = import("./skulpt").pyList;
    type pyTuple = import("./skulpt").pyTuple;
    type pyDict = import("./skulpt").pyDict;
    type pyFunc = import("./skulpt").pyFunc;
    type pyNone = import("./skulpt").pyNone;

    var DRAFTER_SITE_ROOT_ELEMENT_ID: string;
}

export {};
