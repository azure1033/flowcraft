/** Custom node component registry for React Flow. */

import PlannerNode from './PlannerNode';
import ExecutorNode from './ExecutorNode';
import ReviewerNode from './ReviewerNode';
import ToolNode from './ToolNode';

export const nodeTypes = {
  planner: PlannerNode,
  executor: ExecutorNode,
  reviewer: ReviewerNode,
  tool: ToolNode,
};

export { PlannerNode, ExecutorNode, ReviewerNode, ToolNode };
