// Figma Plugin - Template Automation
// This plugin applies text replacements and style changes to Figma templates

figma.showUI(__html__, { width: 400, height: 600 });

figma.ui.onmessage = async (msg) => {
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
              const hex = config.fill.replace('#', '');
              const r = parseInt(hex.substr(0, 2), 16) / 255;
              const g = parseInt(hex.substr(2, 2), 16) / 255;
              const b = parseInt(hex.substr(4, 2), 16) / 255;

              node.fills = [{ type: 'SOLID', color: { r, g, b } }];
            }

            // Apply stroke color
            if (config.stroke && 'strokes' in node) {
              const hex = config.stroke.replace('#', '');
              const r = parseInt(hex.substr(0, 2), 16) / 255;
              const g = parseInt(hex.substr(2, 2), 16) / 255;
              const b = parseInt(hex.substr(4, 2), 16) / 255;

              node.strokes = [{ type: 'SOLID', color: { r, g, b } }];
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
