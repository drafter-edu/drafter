export default {
    preset: "ts-jest/presets/default-esm",
    testEnvironment: "jsdom",
    extensionsToTreatAsEsm: [".ts", ".tsx"],
    setupFilesAfterEnv: ["<rootDir>/src/__tests__/setup.ts"],
    moduleNameMapper: {
        "^(\\.{1,2}/.*)\\.js$": "$1",
    },
    transform: {
        "^.+\\.tsx?$": [
            "ts-jest",
            {
                useESM: true,
                tsconfig: "tsconfig.jest.json",
            },
        ],
    },
    testMatch: [
        "**/__tests__/**/*.test.{ts,tsx}",
        "**/__tests__/**/*.test.{js,jsx}",
    ],
    collectCoverageFrom: [
        "src/**/*.{ts,tsx}",
        "!src/**/*.d.ts",
        "!src/**/__tests__/**",
    ],
    testTimeout: 30000,
};
