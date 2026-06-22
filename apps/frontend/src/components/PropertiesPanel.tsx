import { useState, useEffect } from 'react';
import { useWorkflowStore } from '../stores/workflowStore';
import type { WorkflowNode } from '../types/workflow';

export default function PropertiesPanel() {
  const { nodes, selectedNodeId, updateNode, removeNode } = useWorkflowStore();
  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || null;

  if (!selectedNode) {
    return (
      <div style={panelStyle}>
        <p style={{ color: '#999', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
          Select a node to edit properties
        </p>
      </div>
    );
  }

  return (
    <div style={panelStyle}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: 14 }}>Properties</h3>
      <p style={{ fontSize: 12, color: '#666', marginBottom: 16 }}>
        ID: {selectedNode.id} | Type: {selectedNode.type}
      </p>

      {/* Executor / Reviewer: tools binding */}
      {(selectedNode.type === 'executor' || selectedNode.type === 'reviewer') && (
        <PropertyGroup label="Tools (comma-separated)">
          <input
            style={inputStyle}
            value={(selectedNode.tools || []).join(', ')}
            onChange={(e) =>
              updateNode(selectedNode.id, {
                tools: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
              })
            }
            placeholder="search, code_exec, http_request"
          />
        </PropertyGroup>
      )}

      {/* Reviewer: human confirm toggle */}
      {selectedNode.type === 'reviewer' && (
        <PropertyGroup label="Human Confirmation">
          <label style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
            <input
              type="checkbox"
              checked={!!selectedNode.human_confirm}
              onChange={(e) => updateNode(selectedNode.id, { human_confirm: e.target.checked })}
            />
            Require manual approval
          </label>
        </PropertyGroup>
      )}

      {/* Tool: tool name */}
      {selectedNode.type === 'tool' && (
        <PropertyGroup label="Tool Name">
          <input
            style={inputStyle}
            value={selectedNode.tool_name || ''}
            onChange={(e) => updateNode(selectedNode.id, { tool_name: e.target.value })}
            placeholder="search"
          />
        </PropertyGroup>
      )}

      {/* Delete */}
      <div style={{ marginTop: 24 }}>
        <button
          onClick={() => removeNode(selectedNode.id)}
          style={{
            padding: '6px 16px',
            borderRadius: 4,
            border: '1px solid #e53935',
            background: '#fff',
            color: '#e53935',
            cursor: 'pointer',
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          Delete Node
        </button>
      </div>
    </div>
  );
}

function PropertyGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ fontSize: 12, fontWeight: 600, color: '#555', display: 'block', marginBottom: 4 }}>
        {label}
      </label>
      {children}
    </div>
  );
}

const panelStyle: React.CSSProperties = {
  width: 240,
  background: '#fafafa',
  borderLeft: '1px solid #e0e0e0',
  padding: 16,
  fontFamily: 'system-ui, sans-serif',
  overflowY: 'auto',
};

const inputStyle: React.CSSProperties = {
  width: 'calc(100% - 16px)',
  padding: '6px 8px',
  borderRadius: 4,
  border: '1px solid #ddd',
  fontSize: 12,
  outline: 'none',
};
