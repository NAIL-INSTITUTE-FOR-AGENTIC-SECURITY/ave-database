import * as vscode from 'vscode';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AVECard {
  ave_id: string;
  name: string;
  category: string;
  severity: string;
  status: string;
  summary: string;
  mechanism: string;
  defences: string[];
  mitre_mapping: string;
  cwe_mapping: string;
  avss_score: string;
  references: string[];
  related_aves: string[];
}

// ---------------------------------------------------------------------------
// Data Provider
// ---------------------------------------------------------------------------

class AVETreeItem extends vscode.TreeItem {
  constructor(
    public readonly card: AVECard,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
  ) {
    super(`${card.ave_id} — ${card.name}`, collapsibleState);
    this.tooltip = `${card.ave_id}: ${card.name}\n${card.summary}`;
    this.description = `${card.severity.toUpperCase()} | ${card.category}`;
    this.iconPath = this.getSeverityIcon(card.severity);
    this.command = {
      command: 'ave.showCard',
      title: 'Show Card',
      arguments: [card],
    };
  }

  private getSeverityIcon(severity: string): vscode.ThemeIcon {
    switch (severity.toLowerCase()) {
      case 'critical':
        return new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
      case 'high':
        return new vscode.ThemeIcon('warning', new vscode.ThemeColor('editorWarning.foreground'));
      case 'medium':
        return new vscode.ThemeIcon('info', new vscode.ThemeColor('editorInfo.foreground'));
      default:
        return new vscode.ThemeIcon('circle-outline');
    }
  }
}

class CategoryItem extends vscode.TreeItem {
  constructor(
    public readonly category: string,
    public readonly cards: AVECard[],
  ) {
    super(category, vscode.TreeItemCollapsibleState.Collapsed);
    this.description = `${cards.length} cards`;
    this.iconPath = new vscode.ThemeIcon('folder');
  }
}

class AVEDataProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<vscode.TreeItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
  private cards: AVECard[] = [];
  private groupBy: 'category' | 'severity' = 'category';

  constructor(private apiUrl: string) {}

  setGroupBy(mode: 'category' | 'severity') {
    this.groupBy = mode;
    this._onDidChangeTreeData.fire(undefined);
  }

  async refresh(): Promise<void> {
    try {
      const response = await fetch(`${this.apiUrl}/api/v2/ave`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json() as { cards: AVECard[] };
      this.cards = data.cards || [];
      this._onDidChangeTreeData.fire(undefined);
      vscode.window.showInformationMessage(
        `AVE Database: loaded ${this.cards.length} cards`
      );
    } catch (err) {
      vscode.window.showErrorMessage(
        `Failed to fetch AVE database: ${err}`
      );
    }
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: vscode.TreeItem): vscode.TreeItem[] {
    if (!element) {
      // Root level: group by category or severity
      const groups = new Map<string, AVECard[]>();
      const key = this.groupBy;
      for (const card of this.cards) {
        const group = card[key] || 'unknown';
        if (!groups.has(group)) {
          groups.set(group, []);
        }
        groups.get(group)!.push(card);
      }

      return Array.from(groups.entries())
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([name, cards]) => new CategoryItem(name, cards));
    }

    if (element instanceof CategoryItem) {
      return element.cards
        .sort((a, b) => a.ave_id.localeCompare(b.ave_id))
        .map(card => new AVETreeItem(card, vscode.TreeItemCollapsibleState.None));
    }

    return [];
  }

  search(query: string): AVECard[] {
    const q = query.toLowerCase();
    return this.cards.filter(card =>
      card.ave_id.toLowerCase().includes(q) ||
      card.name.toLowerCase().includes(q) ||
      card.summary.toLowerCase().includes(q) ||
      card.category.toLowerCase().includes(q) ||
      card.mitre_mapping.toLowerCase().includes(q)
    );
  }
}

// ---------------------------------------------------------------------------
// Card Detail View
// ---------------------------------------------------------------------------

function showCardWebview(card: AVECard, context: vscode.ExtensionContext): void {
  const panel = vscode.window.createWebviewPanel(
    'aveCard',
    `${card.ave_id} — ${card.name}`,
    vscode.ViewColumn.One,
    { enableScripts: false },
  );

  const severityColor = {
    critical: '#e53e3e',
    high: '#dd6b20',
    medium: '#d69e2e',
    low: '#38a169',
  }[card.severity.toLowerCase()] || '#718096';

  const defencesHtml = card.defences?.length
    ? '<ul>' + card.defences.map(d => `<li>${escapeHtml(d)}</li>`).join('') + '</ul>'
    : '<p>None documented</p>';

  const referencesHtml = card.references?.length
    ? '<ul>' + card.references.map(r => `<li><a href="${escapeHtml(r)}">${escapeHtml(r)}</a></li>`).join('') + '</ul>'
    : '<p>None</p>';

  const relatedHtml = card.related_aves?.length
    ? card.related_aves.map(r => `<code>${escapeHtml(r)}</code>`).join(', ')
    : 'None';

  panel.webview.html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: var(--vscode-font-family); padding: 20px; color: var(--vscode-foreground); }
    h1 { margin-bottom: 4px; }
    .severity { display: inline-block; padding: 2px 10px; border-radius: 4px; color: white; background: ${severityColor}; font-weight: bold; text-transform: uppercase; }
    .meta { color: var(--vscode-descriptionForeground); margin: 8px 0; }
    .section { margin: 16px 0; }
    .section h2 { border-bottom: 1px solid var(--vscode-panel-border); padding-bottom: 4px; }
    code { background: var(--vscode-textCodeBlock-background); padding: 1px 4px; border-radius: 3px; }
    .mitre { font-family: monospace; background: var(--vscode-textCodeBlock-background); padding: 8px; border-radius: 4px; }
    ul { padding-left: 20px; }
    a { color: var(--vscode-textLink-foreground); }
  </style>
</head>
<body>
  <h1>${escapeHtml(card.ave_id)}</h1>
  <h2>${escapeHtml(card.name)}</h2>
  <span class="severity">${escapeHtml(card.severity)}</span>
  <p class="meta">Category: <strong>${escapeHtml(card.category)}</strong>
    ${card.avss_score ? ` | AVSS: <strong>${escapeHtml(card.avss_score)}</strong>` : ''}
    | Status: ${escapeHtml(card.status)}</p>

  <div class="section">
    <h2>Summary</h2>
    <p>${escapeHtml(card.summary)}</p>
  </div>

  <div class="section">
    <h2>Mechanism</h2>
    <p>${escapeHtml(card.mechanism || 'Not documented')}</p>
  </div>

  <div class="section">
    <h2>MITRE Mapping</h2>
    <div class="mitre">${escapeHtml(card.mitre_mapping || 'None')}</div>
  </div>

  ${card.cwe_mapping ? `<div class="section"><h2>CWE Mapping</h2><code>${escapeHtml(card.cwe_mapping)}</code></div>` : ''}

  <div class="section">
    <h2>Defences</h2>
    ${defencesHtml}
  </div>

  <div class="section">
    <h2>Related AVEs</h2>
    <p>${relatedHtml}</p>
  </div>

  <div class="section">
    <h2>References</h2>
    ${referencesHtml}
  </div>
</body>
</html>`;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ---------------------------------------------------------------------------
// Extension Activation
// ---------------------------------------------------------------------------

export function activate(context: vscode.ExtensionContext) {
  const config = vscode.workspace.getConfiguration('ave');
  const apiUrl = config.get<string>('apiUrl', 'https://api.nailinstitute.org');

  const categoryProvider = new AVEDataProvider(apiUrl);
  const severityProvider = new AVEDataProvider(apiUrl);
  severityProvider.setGroupBy('severity');

  vscode.window.registerTreeDataProvider('aveExplorer', categoryProvider);
  vscode.window.registerTreeDataProvider('aveSeverity', severityProvider);

  // Commands
  context.subscriptions.push(
    vscode.commands.registerCommand('ave.refresh', async () => {
      await categoryProvider.refresh();
      await severityProvider.refresh();
    }),

    vscode.commands.registerCommand('ave.search', async () => {
      const query = await vscode.window.showInputBox({
        placeHolder: 'Search AVE cards (e.g., "injection", "T1027", "critical")',
        prompt: 'Search the AVE database',
      });
      if (!query) { return; }

      const results = categoryProvider.search(query);
      if (results.length === 0) {
        vscode.window.showInformationMessage(`No AVE cards matching "${query}"`);
        return;
      }

      const items = results.map(card => ({
        label: `${card.ave_id} — ${card.name}`,
        description: `${card.severity.toUpperCase()} | ${card.category}`,
        detail: card.summary,
        card,
      }));

      const selected = await vscode.window.showQuickPick(items, {
        placeHolder: `${results.length} results for "${query}"`,
        matchOnDescription: true,
        matchOnDetail: true,
      });

      if (selected) {
        showCardWebview(selected.card, context);
      }
    }),

    vscode.commands.registerCommand('ave.showCard', (card: AVECard) => {
      showCardWebview(card, context);
    }),

    vscode.commands.registerCommand('ave.openMitre', (card: AVECard) => {
      const mitre = card.mitre_mapping;
      if (!mitre) {
        vscode.window.showInformationMessage('No MITRE mapping for this card');
        return;
      }

      // Extract technique IDs and open MITRE page
      const attackMatch = mitre.match(/T\d{4}(?:\.\d{3})?/g);
      const atlasMatch = mitre.match(/AML\.T\d{4}/g);

      if (attackMatch) {
        vscode.env.openExternal(
          vscode.Uri.parse(`https://attack.mitre.org/techniques/${attackMatch[0].replace('.', '/')}/`)
        );
      } else if (atlasMatch) {
        vscode.env.openExternal(
          vscode.Uri.parse(`https://atlas.mitre.org/techniques/${atlasMatch[0]}`)
        );
      }
    }),
  );

  // Auto-refresh on activation
  if (config.get<boolean>('autoRefresh', false)) {
    categoryProvider.refresh();
    severityProvider.refresh();
  }

  console.log('NAIL AVE Browser extension activated');
}

export function deactivate() {}
