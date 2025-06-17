const path = require('path');

module.exports = {
  webpack: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  style: {
    postcss: {
      plugins: [require('autoprefixer')],
    },
  },
  jest: {
    configure: (jestConfig, { env, paths, resolve, rootDir }) => {
      return {
        ...jestConfig,
        setupFiles: [...jestConfig.setupFiles, './src/config/__mocks__/dom.js'],
        moduleFileExtensions: [...jestConfig.moduleFileExtensions, 'ts', 'tsx']
      };
    }
  },
};
