// Figma Plugin - Template Automation
// This plugin applies text replacements and style changes to Figma templates

figma.showUI(__html__, { width: 400, height: 600 });

// Helper: Convert hex color to RGB (0-1 range)
function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const clean = hex.replace('#', '');
  const r = parseInt(clean.substr(0, 2), 16) / 255;
  const g = parseInt(clean.substr(2, 2), 16) / 255;
  const b = parseInt(clean.substr(4, 2), 16) / 255;
  return { r, g, b };
}

// Helper: Find all text nodes in current page
function findAllTextNodes(): TextNode[] {
  return figma.currentPage.findAll((n) => n.type === 'TEXT') as TextNode[];
}

// Helper: Get template information
function getTemplateInfo() {
  const selection = figma.currentPage.selection;

  if (selection.length === 0) {
    return {
      error: 'Please select a frame or component to analyze'
    };
  }

  const node = selection[0];
  const textNodes: Array<{ name: string; characters: string; fontName: string }> = [];

  // Find all text nodes within the selected node
  if ('findAll' in node) {
    const texts = node.findAll((n) => n.type === 'TEXT') as TextNode[];

    for (const text of texts) {
      textNodes.push({
        name: text.name,
        characters: text.characters,
        fontName: typeof text.fontName === 'object' ? text.fontName.family : 'Mixed'
      });
    }
  }

  return {
    id: node.id,
    name: node.name,
    type: node.type,
    width: 'width' in node ? node.width : 0,
    height: 'height' in node ? node.height : 0,
    textNodes: textNodes
  };
}

figma.ui.onmessage = async (msg) => {
  // Get template information
  if (msg.type === 'get-template-info') {
    const info = getTemplateInfo();
    figma.ui.postMessage({ type: 'template-info', data: info });
    return;
  }

  // Apply template changes
  if (msg.type === 'apply-template') {
    const { jobId, fields, colors } = msg;

    try {
      // Apply text replacements
      if (fields) {
        for (const [nodeId, text] of Object.entries(fields)) {
          const nodes = figma.currentPage.findAll((n) => n.name === nodeId);
          for (const node of nodes) {
            if (node.type === 'TEXT') {
              await figma.loadFontAsync(node.fontName as FontName);
              node.characters = text as string;
            }
          }
        }
      }

      // Apply color changes
      if (colors) {
        for (const [nodeId, colorConfig] of Object.entries(colors)) {
          const nodes = figma.currentPage.findAll((n) => n.name === nodeId);
          for (const node of nodes) {
            const config = colorConfig as any;

            // Apply fill color
            if (config.fill && 'fills' in node) {
              const rgb = hexToRgb(config.fill);
              node.fills = [{ type: 'SOLID', color: rgb }];
            }

            // Apply stroke color
            if (config.stroke && 'strokes' in node) {
              const rgb = hexToRgb(config.stroke);
              node.strokes = [{ type: 'SOLID', color: rgb }];
            }

            // Apply stroke width
            if (config.stroke_width_px && 'strokeWeight' in node) {
              node.strokeWeight = config.stroke_width_px;
            }
          }
        }
      }

      figma.ui.postMessage({ type: 'apply-success', jobId });
      figma.notify('Template applied successfully!');

    } catch (error) {
      figma.ui.postMessage({
        type: 'apply-error',
        jobId,
        error: (error as Error).message
      });
      figma.notify('Error applying template', { error: true });
    }
  }

  if (msg.type === 'export-template') {
    const { format, scale } = msg;

    try {
      const selection = figma.currentPage.selection;
      if (selection.length === 0) {
        figma.notify('Please select a frame to export', { error: true });
        return;
      }

      const node = selection[0];
      const settings: ExportSettings = {
        format: format.toUpperCase(),
        constraint: { type: 'SCALE', value: scale || 2 }
      };

      const bytes = await node.exportAsync(settings);

      figma.ui.postMessage({
        type: 'export-success',
        data: Array.from(bytes),
        format
      });
      figma.notify(`Exported as ${format.toUpperCase()}`);

    } catch (error) {
      figma.ui.postMessage({
        type: 'export-error',
        error: (error as Error).message
      });
      figma.notify('Error exporting', { error: true });
    }
  }

  if (msg.type === 'cancel') {
    figma.closePlugin();
  }
};
