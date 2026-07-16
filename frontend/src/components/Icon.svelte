<script>
  import { icons } from '../lib/icons.js';

  let { name = 'dashboard', size = 20, class: className = '' } = $props();
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
  {@html icons[name] || ''}
</svg>
