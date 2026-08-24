"use client";
import { jsx } from 'react/jsx-runtime';
import { invariant } from 'motion-utils';
import { forwardRef, useRef, useState, useEffect } from 'react';
import { ReorderContext } from '../../context/ReorderContext.mjs';
import { motion } from '../../render/components/motion/proxy.mjs';
import { useConstant } from '../../utils/use-constant.mjs';
import { checkReorder } from './utils/check-reorder.mjs';
import { detectAxis } from './utils/detect-axis.mjs';

function ReorderGroupComponent({ children, as = "ul", axis: axisOverride, onReorder, values, ...props }, externalRef) {
    const Component = useConstant(() => motion[as]);
    const itemLayouts = useRef(new Map());
    const [detectedAxis, setDetectedAxis] = useState("y");
    const isReordering = useRef(false);
    const groupRef = useRef(null);
    const axis = axisOverride || detectedAxis;
    invariant(Boolean(values), "Reorder.Group must be provided a values prop", "reorder-values");
    const valuesSet = new Set(values);
    itemLayouts.current.forEach((_, value) => {
        if (!valuesSet.has(value))
            itemLayouts.current.delete(value);
    });
    const context = {
        axis,
        groupRef,
        registerItem: (value, layout) => {
            itemLayouts.current.set(value, layout);
            if (!axisOverride) {
                const nextAxis = detectAxis(values.flatMap((itemValue) => {
                    const itemLayout = itemLayouts.current.get(itemValue);
                    return itemLayout ? [itemLayout] : [];
                }));
                if (nextAxis !== detectedAxis)
                    setDetectedAxis(nextAxis);
            }
        },
        updateOrder: (item, offset, velocity) => {
            if (isReordering.current)
                return;
            const order = values.flatMap((value) => {
                const layout = itemLayouts.current.get(value);
                return layout ? [{ value, layout }] : [];
            });
            const direction = groupRef.current?.ownerDocument.defaultView?.getComputedStyle(groupRef.current).direction === "rtl"
                ? "rtl"
                : "ltr";
            const newOrder = checkReorder(order, item, offset, velocity, axis, direction);
            if (order !== newOrder) {
                isReordering.current = true;
                const newValues = [...values];
                const measuredIndexes = order.map(({ value }) => values.indexOf(value));
                newOrder.forEach(({ value }, index) => {
                    newValues[measuredIndexes[index]] = value;
                });
                onReorder(newValues);
            }
        },
    };
    useEffect(() => {
        isReordering.current = false;
    });
    // Combine refs if external ref is provided
    const setRef = (element) => {
        groupRef.current = element;
        if (typeof externalRef === "function") {
            externalRef(element);
        }
        else if (externalRef) {
            externalRef.current =
                element;
        }
    };
    /**
     * Disable browser scroll anchoring on the group container.
     * When items reorder, scroll anchoring can cause the browser to adjust
     * the scroll position, which interferes with drag position calculations.
     */
    const groupStyle = {
        overflowAnchor: "none",
        ...props.style,
    };
    return (jsx(Component, { ...props, style: groupStyle, ref: setRef, ignoreStrict: true, children: jsx(ReorderContext.Provider, { value: context, children: children }) }));
}
const ReorderGroup = /*@__PURE__*/ forwardRef(ReorderGroupComponent);

export { ReorderGroup, ReorderGroupComponent };
//# sourceMappingURL=Group.mjs.map
