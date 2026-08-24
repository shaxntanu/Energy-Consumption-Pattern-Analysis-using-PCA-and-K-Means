import { invariant } from 'motion-utils';
import { isCSSVariableName } from '../../animation/utils/is-css-variable.mjs';
import { transformProps } from '../utils/keys-transform.mjs';
import { defaultTransformValue, readTransformValue } from '../dom/parse-transform.mjs';
import { measureViewportBox } from '../../projection/utils/measure.mjs';
import { DOMVisualElement } from '../dom/DOMVisualElement.mjs';
import { buildHTMLStyles } from './utils/build-styles.mjs';
import { renderHTML } from './utils/render.mjs';
import { scrapeMotionValuesFromProps } from './utils/scrape-motion-values.mjs';

function getComputedStyle(element) {
    return window.getComputedStyle(element);
}
class HTMLVisualElement extends DOMVisualElement {
    constructor() {
        super(...arguments);
        this.type = "html";
        this.renderInstance = renderHTML;
    }
    mount(instance) {
        /**
         * If a custom component forwards its ref to something other than a
         * HTML/SVG element (a class instance, an imperative handle) there's
         * nothing for Motion to style, measure or attach gestures to. #2777
         */
        invariant(Boolean(instance.style), "motion.create() components must forward their ref to a HTML or SVG element", "custom-component-ref");
        super.mount(instance);
    }
    readValueFromInstance(instance, key) {
        if (transformProps.has(key)) {
            return this.projection?.isProjecting
                ? defaultTransformValue(key)
                : readTransformValue(instance, key);
        }
        else {
            const computedStyle = getComputedStyle(instance);
            const value = (isCSSVariableName(key)
                ? computedStyle.getPropertyValue(key)
                : computedStyle[key]) || 0;
            return typeof value === "string" ? value.trim() : value;
        }
    }
    measureInstanceViewportBox(instance, { transformPagePoint }) {
        return measureViewportBox(instance, transformPagePoint);
    }
    build(renderState, latestValues, props) {
        buildHTMLStyles(renderState, latestValues, props.transformTemplate);
    }
    scrapeMotionValuesFromProps(props, prevProps, visualElement) {
        return scrapeMotionValuesFromProps(props, prevProps, visualElement);
    }
}

export { HTMLVisualElement, getComputedStyle };
//# sourceMappingURL=HTMLVisualElement.mjs.map
