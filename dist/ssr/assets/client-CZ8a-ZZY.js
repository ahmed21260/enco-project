import { R as React, j as jsxRuntimeExports } from "../index.js";
import "../__vite_rsc_assets_manifest.js";
function ClientCounter() {
  const [count, setCount] = React.useState(0);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { onClick: () => setCount((count2) => count2 + 1), children: [
    "Client Counter: ",
    count
  ] });
}
export {
  ClientCounter
};
