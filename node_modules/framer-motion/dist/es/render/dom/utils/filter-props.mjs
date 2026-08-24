import { isMotionValue } from 'motion-dom';
import { isValidMotionProp } from '../../../motion/utils/valid-prop.mjs';

function shouldForward(key, isValidProp) {
    return key.startsWith("on")
        ? !isValidMotionProp(key)
        : isValidProp?.(key) ?? !isValidMotionProp(key);
}
function filterProps(props, isDom, forwardMotionProps, isValidProp) {
    const filteredProps = {};
    for (const key in props) {
        /**
         * values is considered a valid prop by Emotion, so if it's present
         * this will be rendered out to the DOM unless explicitly filtered.
         *
         * We check the type as it could be used with the `feColorMatrix`
         * element, which we support.
         */
        if (key === "values" && typeof props.values === "object")
            continue;
        if (isMotionValue(props[key]))
            continue;
        if (shouldForward(key, isValidProp) ||
            (forwardMotionProps === true && isValidMotionProp(key)) ||
            (!isDom && !isValidMotionProp(key)) ||
            // If trying to use native HTML drag events, forward drag listeners
            (props["draggable"] &&
                key.startsWith("onDrag"))) {
            filteredProps[key] =
                props[key];
        }
    }
    return filteredProps;
}

export { filterProps };
//# sourceMappingURL=filter-props.mjs.map
