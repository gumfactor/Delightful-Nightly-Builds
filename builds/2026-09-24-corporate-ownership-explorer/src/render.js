/**
 * DOM rendering. Every function here builds nodes with createElement and
 * assigns text with textContent only — never innerHTML — so that no label
 * or description coming back from the Wikidata API (which is external,
 * user-editable data) can ever be parsed as markup. Exposed as
 * window.OwnershipRender.
 */
(function (global) {
  'use strict';

  function clearChildren(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
  }

  function el(tag, options) {
    const node = document.createElement(tag);
    const { text, className, attrs } = options || {};
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    if (attrs) {
      for (const [key, value] of Object.entries(attrs)) {
        node.setAttribute(key, value);
      }
    }
    return node;
  }

  function citationLink(url) {
    if (!url) return null;
    const a = el('a', {
      text: 'source ↗',
      className: 'citation-link',
      attrs: {
        href: url,
        target: '_blank',
        rel: 'noopener noreferrer',
        'data-testid': 'citation-link',
      },
    });
    return a;
  }

  function propertyLabel(property) {
    if (property === 'P127') return 'owned by';
    if (property === 'P749') return 'parent organization';
    if (property === 'P355') return 'subsidiary';
    return 'related to';
  }

  function renderSearchResults(container, results, onSelect) {
    clearChildren(container);
    if (!results || results.length === 0) {
      container.hidden = true;
      return;
    }
    container.hidden = false;
    for (const result of results) {
      const item = el('li', { className: 'search-result', attrs: { 'data-testid': 'search-result', 'data-id': result.id } });
      const label = el('span', { text: result.label, className: 'result-label' });
      item.appendChild(label);
      if (result.description) {
        item.appendChild(el('span', { text: result.description, className: 'result-description' }));
      }
      item.addEventListener('click', () => onSelect(result));
      container.appendChild(item);
    }
  }

  function renderFocusPanel(container, focus) {
    clearChildren(container);
    if (!focus) {
      container.appendChild(el('p', { text: 'Search for a company to see its ownership chain.', className: 'empty-state' }));
      return;
    }
    const header = el('h2', { text: focus.label, attrs: { 'data-testid': 'focus-label' } });
    container.appendChild(header);
    if (focus.description) {
      container.appendChild(el('p', { text: focus.description, className: 'focus-description' }));
    }
    const qidLink = el('a', {
      text: focus.id,
      className: 'qid-link',
      attrs: {
        href: `https://www.wikidata.org/wiki/${focus.id}`,
        target: '_blank',
        rel: 'noopener noreferrer',
        'data-testid': 'focus-qid-link',
      },
    });
    const qidLine = el('p', { className: 'qid-line' });
    qidLine.appendChild(document.createTextNode('Wikidata: '));
    qidLine.appendChild(qidLink);
    container.appendChild(qidLine);
  }

  function renderChainNode(node, onNodeClick) {
    const item = el('li', { className: 'chain-node', attrs: { 'data-testid': 'chain-node', 'data-id': node.id } });
    const propSpan = el('span', { text: propertyLabel(node.property), className: 'chain-relation' });
    const labelButton = el('button', {
      text: node.label,
      className: 'chain-label',
      attrs: { type: 'button', 'data-testid': 'chain-node-button' },
    });
    labelButton.addEventListener('click', () => onNodeClick(node));
    item.appendChild(propSpan);
    item.appendChild(labelButton);
    if (node.qualifierText) {
      item.appendChild(el('span', { text: `(${node.qualifierText})`, className: 'chain-qualifier' }));
    }
    const link = citationLink(node.statementUrl);
    if (link) item.appendChild(link);
    return item;
  }

  function renderParentChain(container, result, onNodeClick) {
    clearChildren(container);
    const { chain, cycleDetected, depthCapped } = result || { chain: [] };
    if (!chain || chain.length === 0) {
      container.appendChild(el('p', { text: 'No ownership data recorded on Wikidata for this company.', className: 'empty-state', attrs: { 'data-testid': 'parent-chain-empty' } }));
      return;
    }
    const list = el('ul', { className: 'chain-list', attrs: { 'data-testid': 'parent-chain-list' } });
    for (const node of chain) {
      list.appendChild(renderChainNode(node, onNodeClick));
    }
    container.appendChild(list);
    if (cycleDetected) {
      container.appendChild(el('p', { text: 'Ownership loop detected in Wikidata data — chain stopped to avoid looping forever.', className: 'notice', attrs: { 'data-testid': 'cycle-notice' } }));
    }
    if (depthCapped) {
      container.appendChild(el('p', { text: 'Chain continues beyond the display limit (8 links).', className: 'notice', attrs: { 'data-testid': 'depth-notice' } }));
    }
  }

  function renderSubsidiaries(container, subsidiaries, onNodeClick) {
    clearChildren(container);
    if (!subsidiaries || subsidiaries.length === 0) {
      container.appendChild(el('p', { text: 'No subsidiaries recorded on Wikidata for this company.', className: 'empty-state', attrs: { 'data-testid': 'subsidiaries-empty' } }));
      return;
    }
    const list = el('ul', { className: 'chain-list', attrs: { 'data-testid': 'subsidiaries-list' } });
    for (const node of subsidiaries) {
      list.appendChild(renderChainNode(node, onNodeClick));
    }
    container.appendChild(list);
  }

  function renderBreadcrumb(container, history, onJump) {
    clearChildren(container);
    if (!history || history.length === 0) return;
    history.forEach((entry, index) => {
      if (index > 0) {
        container.appendChild(el('span', { text: ' › ', className: 'breadcrumb-sep' }));
      }
      const button = el('button', {
        text: entry.label,
        className: 'breadcrumb-item',
        attrs: { type: 'button', 'data-testid': 'breadcrumb-item' },
      });
      if (index === history.length - 1) {
        button.disabled = true;
        button.classList.add('current');
      } else {
        button.addEventListener('click', () => onJump(index));
      }
      container.appendChild(button);
    });
  }

  function renderRecent(container, recent, onSelect) {
    clearChildren(container);
    if (!recent || recent.length === 0) {
      container.appendChild(el('p', { text: 'No recent searches yet.', className: 'empty-state' }));
      return;
    }
    const list = el('ul', { className: 'recent-list', attrs: { 'data-testid': 'recent-list' } });
    for (const entry of recent) {
      const item = el('li', { attrs: { 'data-testid': 'recent-item' } });
      const button = el('button', { text: entry.label, className: 'recent-item-button', attrs: { type: 'button' } });
      button.addEventListener('click', () => onSelect(entry));
      item.appendChild(button);
      list.appendChild(item);
    }
    container.appendChild(list);
  }

  function renderError(container, message) {
    clearChildren(container);
    if (!message) {
      container.hidden = true;
      return;
    }
    container.hidden = false;
    container.appendChild(el('p', { text: message, attrs: { 'data-testid': 'error-message' } }));
  }

  function setLoading(container, isLoading) {
    container.hidden = !isLoading;
  }

  global.OwnershipRender = {
    renderSearchResults,
    renderFocusPanel,
    renderParentChain,
    renderSubsidiaries,
    renderBreadcrumb,
    renderRecent,
    renderError,
    setLoading,
    propertyLabel,
  };
})(typeof window !== 'undefined' ? window : globalThis);
