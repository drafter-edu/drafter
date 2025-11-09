// postcss.config.cjs
module.exports = {
    plugins: [
        require("postcss-preset-env")({
            stage: 3, // enables modern features safely
            autoprefixer: true, // add vendor prefixes from Browserslist
            features: { "nesting-rules": true },
        }),
    ],
};
