/*****
 * CRACO config to tweak CRA webpack without ejecting.
 * - Suppress source map loader warnings from webcola's missing TS sources
 * - Exclude webcola from source-map-loader to avoid noisy warnings
 *****/

const path = require('path');

module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Disable source-map-loader for webcola paths
      if (webpackConfig.module && Array.isArray(webpackConfig.module.rules)) {
        webpackConfig.module.rules.forEach((rule) => {
          if (rule.use || rule.loader) {
            const oneOf = rule.oneOf || [rule];
            oneOf.forEach((r) => {
              if (r.use) {
                r.use = r.use.map((u) => {
                  if (u && (u.loader || u) && ((u.loader || u).includes('source-map-loader'))) {
                    // Exclude webcola from source-map-loader
                    u.options = u.options || {};
                    const origFilter = u.options.filter || (() => true);
                    u.options.filter = (source, map) => {
                      if (/node_modules\\webcola\\/i.test(source) || /node_modules\/webcola\//i.test(source)) {
                        return false; // ignore webcola
                      }
                      return origFilter(source, map);
                    };
                  }
                  return u;
                });
              }
            });
          }
        });
      }

      // Suppress performance hints from webcola sourcemaps
      webpackConfig.ignoreWarnings = webpackConfig.ignoreWarnings || [];
      webpackConfig.ignoreWarnings.push((warning) => {
        return (
          typeof warning === 'object' && warning &&
          /source map/i.test(String(warning.message || '')) &&
          (/webcola/i.test(String(warning.moduleName || '')) || /webcola/i.test(String(warning.file || '')))
        );
      });

      return webpackConfig;
    },
  },
};
