/**
 * This is a minimal config.
 *
 * If you need the full config, get it from here:
 * https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
 */

module.exports = {
    content: [
        '../templates/**/*.html',
        '../../client/templates/**/*.html',
        '../../client/static/**/*.js',
    ],
    theme: {
        extend: {},
    },
    plugins: [
        /**
         * '@tailwindcss/forms' is the forms plugin that provides a minimal styling
         * for forms. If you don't like it or have own styling for forms,
         * comment the line below to disable '@tailwindcss/forms'.
         */
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography', require("daisyui")),
        require('@tailwindcss/aspect-ratio'),
        require('daisyui'),

        function ({addUtilities, theme}) {
            addUtilities({
                'input[readonly]': {
                    border: 'none',
                    cursor: 'not-allowed',
                },
                'input[readonly="readonly"]': {
                    border: 'none',
                    cursor: 'not-allowed',
                },
                'select[disabled]': {
                    border: 'none',
                    cursor: 'not-allowed',
                },
                'select[disabled="disabled"]': {
                    border: 'none',
                    cursor: 'not-allowed',
                },
            }, {
                variants: ['responsive']
            });
        },

        function ({addComponents}) {
            addComponents({
                '.form-row': {
                    '@apply flex flex-col md:flex-row items-start md:items-center mb-4': {},
                },
                '.form-label': {
                    '@apply w-56 font-medium text-gray-700 mb-1 md:mb-0 pr-4 text-left flex-shrink-0': {},
                },
                '.form-input-wrapper': {
                    '@apply w-full md:flex-1': {},
                },
                '.form-input': {
                    '@apply w-full px-4 py-2 leading-tight input input-bordered': {},
                },
                '.form-error': {
                    '@apply text-red-500 text-sm mt-1': {},
                },
            });
        },
    ],
    daisyui: {
        themes: [
            "light",
            "dark",
            "cupcake",
            "bumblebee",
            "emerald",
            "corporate",
            "synthwave",
            "retro",
            "cyberpunk",
            "valentine",
            "halloween",
            "garden",
            "forest",
            "aqua",
            "lofi",
            "pastel",
            "fantasy",
            "wireframe",
            "black",
            "luxury",
            "dracula",
            "cmyk",
            "autumn",
            "business",
            "acid",
            "lemonade",
            "night",
            "coffee",
            "winter",
            "dim",
            "nord",
            "sunset",
        ],
    },
}
