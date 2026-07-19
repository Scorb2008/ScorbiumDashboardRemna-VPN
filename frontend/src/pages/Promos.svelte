<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatPrice, formatDate } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import Modal from '../components/Modal.svelte';
  import Spinner from '../components/Spinner.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';
  import Icon from '../components/Icon.svelte';

  let promos = $state([]);
  let loading = $state(true);
  let showModal = $state(false);
  let editPromo = $state(null);
  let confirmDelete = $state(false);
  let deleteTarget = $state(null);

  let form = $state({ code: '', discount_type: 'percent', discount_value: 0, discount_percent: 0, discount_amount: 0, max_uses: 0, plan_id: null, expires_at: '', is_active: true });

  async function loadPromos() {
    loading = true;
    try { promos = await api.getPromos({ limit: 200 }); }
    catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadPromos);

  function openCreate() {
    editPromo = null;
    form = { code: '', discount_type: 'percent', discount_value: 0, discount_percent: 0, discount_amount: 0, max_uses: 0, plan_id: null, expires_at: '', is_active: true };
    showModal = true;
  }
  function openEdit(promo) {
    editPromo = promo;
    const hasPercent = promo.discount_percent && promo.discount_percent > 0;
    form = {
      code: promo.code || '',
      discount_type: hasPercent ? 'percent' : 'amount',
      discount_value: hasPercent ? (promo.discount_percent || 0) : (promo.discount_amount || 0),
      discount_percent: promo.discount_percent || 0,
      discount_amount: promo.discount_amount || 0,
      max_uses: promo.max_uses || 0,
      plan_id: promo.plan_id || null,
      expires_at: promo.expires_at || '',
      is_active: promo.is_active !== false
    };
    showModal = true;
  }

  async function savePromo() {
    try {
      const payload = {
        code: form.code,
        max_uses: form.max_uses,
        plan_id: form.plan_id,
        expires_at: form.expires_at || null,
        is_active: form.is_active,
      };
      if (form.discount_type === 'percent') {
        const val = parseFloat(form.discount_value) || 0;
        if (val < 1 || val > 100) return toasts.error('Процент скидки должен быть от 1 до 100');
        payload.discount_percent = val;
        payload.discount_amount = 0;
      } else {
        const val = parseFloat(form.discount_value) || 0;
        if (val <= 0) return toasts.error('Сумма скидки должна быть больше 0');
        payload.discount_amount = val;
        payload.discount_percent = 0;
      }
      if (!form.code?.trim()) return toasts.error('Введите код промокода');
      if (editPromo) { await api.updatePromo(editPromo.id, payload); toasts.success('Промокод обновлён'); }
      else { await api.createPromo(payload); toasts.success('Промокод создан'); }
      showModal = false; await loadPromos();
    } catch (e) { toasts.error(e.message); }
  }

  function askDelete(promo) { deleteTarget = promo; confirmDelete = true; }
  async function doDelete() {
    if (!deleteTarget) return;
    try { await api.deletePromo(deleteTarget.id); toasts.success('Промокод удалён'); await loadPromos(); }
    catch (e) { toasts.error(e.message); }
    confirmDelete = false; deleteTarget = null;
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'code', label: 'Код', sortable: true, render: (r) => `<code class="font-mono text-xs bg-surface-3 px-2 py-1 rounded">${r.code}</code>` },
    { key: 'discount_percent', label: '% Скидки', sortable: true, render: (r) => r.discount_percent ? `${r.discount_percent}%` : '—' },
    { key: 'discount_amount', label: 'Сумма', sortable: true, render: (r) => r.discount_amount ? formatPrice(r.discount_amount) : '—' },
    { key: 'uses_count', label: 'Исп.', sortable: true, render: (r) => `${r.uses_count ?? 0}${r.max_uses ? ' / '+r.max_uses : ''}` },
    { key: 'expires_at', label: 'Истекает', sortable: true, render: (r) => r.expires_at ? `<span class="text-xs text-muted">${formatDate(r.expires_at)}</span>` : '<span class="text-xs text-muted">Бессрочно</span>' },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Промокоды</h1>
      <p class="text-sm text-muted mt-1">{promos.length} промокодов</p>
    </div>
    <button class="btn btn-primary" onclick={openCreate}><Icon name="plus" class="w-4 h-4" /> Новый</button>
  </div>

  <Table columns={columns} data={promos}>
    {#snippet actions(row)}
      <span class="badge {row.is_active !== false ? 'badge-success' : 'badge-danger'}">{row.is_active !== false ? 'Активен' : 'Неактивен'}</span>
      <button class="btn btn-ghost text-muted hover:text-zinc-300" onclick={() => openEdit(row)}><Icon name="pencil" class="w-3.5 h-3.5" /></button>
      <button class="btn btn-ghost text-danger hover:text-danger-hover" onclick={() => askDelete(row)}><Icon name="trash-2" class="w-3.5 h-3.5" /></button>
    {/snippet}
  </Table>
</div>

<Modal bind:open={showModal} title={editPromo ? 'Редактировать промокод' : 'Новый промокод'}>
  <form class="space-y-4" onsubmit={(e) => { e.preventDefault(); savePromo(); }}>
    <div class="space-y-1">
      <label class="label"><span class="label-text">Код</span></label>
      <input type="text" bind:value={form.code} class="input w-full" placeholder="PROMO10" required />
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div class="space-y-1">
        <label class="label"><span class="label-text">Тип скидки</span></label>
        <select bind:value={form.discount_type} class="select w-full">
          <option value="percent">Процент (%)</option>
          <option value="amount">Сумма (₽)</option>
        </select>
      </div>
      <div class="space-y-1">
        <label class="label"><span class="label-text">Значение</span></label>
        <input type="number" bind:value={form.discount_value} class="input w-full" min="0" />
      </div>
      <div class="space-y-1">
        <label class="label"><span class="label-text">Макс. использований (0=∞)</span></label>
        <input type="number" bind:value={form.max_uses} class="input w-full" min="0" />
      </div>
      <div class="space-y-1">
        <label class="label"><span class="label-text">Истекает</span></label>
        <input type="datetime-local" bind:value={form.expires_at} class="input w-full" />
      </div>
    </div>
    <label class="flex items-center gap-2 cursor-pointer">
      <input type="checkbox" bind:checked={form.is_active} class="w-4 h-4 rounded accent-accent" />
      <span class="text-sm">Активен</span>
    </label>
    <div class="flex gap-3 pt-2">
      <button type="button" class="btn btn-secondary flex-1" onclick={() => showModal = false}>Отмена</button>
      <button type="submit" class="btn btn-primary flex-1">{editPromo ? 'Сохранить' : 'Создать'}</button>
    </div>
  </form>
</Modal>

<ConfirmDialog bind:show={confirmDelete} title="Удалить промокод?" message={`Удалить «${deleteTarget?.code}»?`} confirmText="Удалить" danger onConfirm={doDelete} />
