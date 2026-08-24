"use client";
import { jsx } from 'react/jsx-runtime';
import { isMotionValue } from 'motion-dom';
import { invariant } from 'motion-utils';
import { forwardRef, useContext } from 'react';
import { ReorderContext } from '../../context/ReorderContext.mjs';
import { motion } from '../../render/components/motion/proxy.mjs';
import { useConstant } from '../../utils/use-constant.mjs';
import { useMotionValue } from '../../value/use-motion-value.mjs';
import { useTransform } from '../../value/use-transform.mjs';
import { autoScrollIfNeeded, resetAutoScrollState } from './utils/auto-scroll.mjs';

function useDefaultMotionValue(value, defaultValue = 0) {
    return isMotionValue(value) ? value : useMotionValue(defaultValue);
}
function ReorderItemComponent({ children, style = {}, value, as = "li", onDrag, onDragEnd, layout = true, ...props }, externalRef) {
    const Component = useConstant(() => motion[as]);
    const context = useContext(ReorderContext);
    const point = {
        x: useDefaultMotionValue(style.x),
        y: useDefaultMotionValue(style.y),
    };
    const zIndex = useTransform([point.x, point.y], ([latestX, latestY]) => latestX || latestY ? 1 : "unset");
    invariant(Boolean(context), "Reorder.Item must be a child of Reorder.Group", "reorder-item-child");
    const { axis, registerItem, updateOrder, groupRef } = context;
    const dragAxis = axis === "xy" ? true : axis;
    return (jsx(Component, { drag: dragAxis, ...props, dragSnapToOrigin: true, style: { ...style, x: point.x, y: point.y, zIndex }, layout: layout, onDrag: (event, gesturePoint) => {
            const { velocity, point: pointerPoint } = gesturePoint;
            const offset = { x: point.x.get(), y: point.y.get() };
            updateOrder(value, offset, velocity);
            const scrollAxis = axis === "xy"
                ? Math.abs(velocity.x) > Math.abs(velocity.y)
                    ? "x"
                    : "y"
                : axis;
            autoScrollIfNeeded(groupRef.current, pointerPoint[scrollAxis], scrollAxis, velocity[scrollAxis]);
            onDrag && onDrag(event, gesturePoint);
        }, onDragEnd: (event, gesturePoint) => {
            resetAutoScrollState();
            onDragEnd && onDragEnd(event, gesturePoint);
        }, onLayoutMeasure: (measured) => {
            registerItem(value, measured);
        }, ref: externalRef, ignoreStrict: true, children: children }));
}
const ReorderItem = /*@__PURE__*/ forwardRef(ReorderItemComponent);

export { ReorderItem, ReorderItemComponent };
//# sourceMappingURL=Item.mjs.map
