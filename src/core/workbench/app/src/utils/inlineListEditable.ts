export const objectMap = <V, R>(obj: { [key: string]: V }, fn: (value: V, key: string) => R) =>
  Object.keys(obj).reduce((result: { [key: string]: R }, k: string) => {
    const nv = fn(obj[k], k);
    if (nv !== undefined) {
      result[k] = nv;
    }
    return result;
  }, {});
