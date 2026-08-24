import { u as useSWR } from '../use-swr-emll9s78.mjs';
export { S as SWRConfig } from '../use-swr-emll9s78.mjs';
import { s as serialize } from '../config-context-ext53wcz.mjs';
export { k as mutate, l as unload } from '../config-context-ext53wcz.mjs';
export { preload, useSWRConfig } from '../_internal/index.mjs';

const unstable_serialize = (key)=>serialize(key)[0];

// useSWR

export { useSWR as default, unstable_serialize };
