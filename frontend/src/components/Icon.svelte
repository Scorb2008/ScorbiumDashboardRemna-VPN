<script>
  import { icons } from '../lib/icons.js';

  let { name = 'dashboard', size = 20, class: className = '' } = $props();

  function toCamelCase(str) {
    return str.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
  }

  const iconName = $derived(toCamelCase(name));
</script>

<svg
  class="shrink-0 {className}"
  width={size}
  height={size}
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round">
  {@html icons[iconName] || ''}
</svg>
