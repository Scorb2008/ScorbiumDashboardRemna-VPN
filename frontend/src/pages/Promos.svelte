<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import Table from '../components/Table.svelte';
  import Modal from '../components/Modal.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';
  import Spinner from '../components/Spinner.svelte';

  let promos = $state([]);
  let loading = $state(true);
  let showModal = $state(false);
  let showDelete = $state(false);
  let editing = $state(null);
  let form = $state({ code: '', promo_type: 'discount', value: 0, plan_id: null, max_uses: 0 });

  async function loadPromos() {
    loading = true;
    try {
      promos = await api.getPromos();
    } catch (e) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  onMount(loadPromos);

  async function handleSave() {
    try {
      await api.createPromo(form);
      toasts.success('Промокод создан');
      showModal = false;
      await loadPromos();
    } catch (e) {
      toasts.error(e.message);
    }
  }

  async function handleToggle(promo) {
    try {
      await api.togglePromo(promo.id);
      toasts.success('Статус изменён');
      await loadPromos();
    } catch (e) {
      toasts.error(e.message);
    }
  }

  async function handleDelete() {
    if (!editing) return;
    try {
      await api.deletePromo(editing.id);
      toasts.success('Удалён');
      showDelete = false;
      await loadPromos();
    } catch (e) {
      toasts.error(e.message);
    }
  }

  function typeLabel(t) {
    return { discount: 'Скидка', balance: 'Баланс', days: 'Дни' }[t] || t;
  }

  function typeBadge(t) {
    return { discount: 'badge-info', balance: 'badge-success', days: 'badge-primary' }[t] || 'badge-ghost';
  }

  function valueDisplay(r) {
    if (r.promo_type === 'days') return `${r.value} дн.`;
    if (r.promo_type === 'discount') return `${r.value}%`;
    return `${r.value} RUB`;
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'code', label: 'Код', sortable: true, render: (r) => `<span class="font-mono font-medium text-primary">${r.code}</span>` },
    { key: 'promo_type', label: 'Тип', render: (r) => `<span class="badge badge-sm badge-glow ${typeBadge(r.promo_type)}">${typeLabel(r.promo_type)}</span>` },
    { key: 'value', label: 'Значение', sortable: true, render: (r) => `<span class="font-medium">${valueDisplay(r)}</span>` },
    { key: 'max_uses', label: 'Лимит', sortable: true },
    { key: 'current_uses', label: 'Использовано', sortable: true },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-bold">Промокоды</h1>
      <p class="text-sm text-base-content/40 mt-1">{promos.length} промокодов</p>
    </div>
    <button onclick={() => { editing = null; form = { code: '', promo_type: 'discount', value: 0, plan_id: null, max_uses: 0 }; showModal = true; }} class="btn btn-primary btn-sm btn-glow gap-2">
      Создать
    </button>
  </div>

  <Table columns={columns} data={promos}>
    {#snippet actions(row)}
      <div class="flex items-center gap-2">
        <span class="badge badge-sm {row.is_active ? 'badge-success' : 'badge-ghost'}">{row.is_active ? 'Активен' : 'Выкл'}</span>
        <button class="btn btn-xs btn-ghost" onclick={() => handleToggle(row)}>Перекл.</button>
        <button class="btn btn-xs btn-error btn-ghost" onclick={() => { editing = row; showDelete = true; }}>Удалить</button>
      </div>
    {/snippet}
  </Table>
</div>

<Modal bind:open={showModal} title="Новый промокод" size="md">
  <div class="space-y-4">
    <div class="form-control">
      <label class="label"><span class="label-text text-xs font-medium">Код</span></label>
      <input type="text" bind:value={form.code} class="input input-bordered input-glass font-mono" placeholder="SUMMER2024" />
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div class="form-control">
        <label class="label"><span class="label-text text-xs font-medium">Тип</span></label>
        <select bind:value={form.promo_type} class="select select-bordered input-glass">
          <option value="discount">Скидка (%)</option>
          <option value="balance">Баланс (RUB)</option>
          <option value="days">Дни</option>
        </select>
      </div>
      <div class="form-control">
        <label class="label"><span class="label-text text-xs font-medium">Значение</span></label>
        <input type="number" bind:value={form.value} class="input input-bordered input-glass" min="0" />
      </div>
    </div>
    <div class="form-control">
      <label class="label"><span class="label-text text-xs font-medium">Лимит (0 = безлимит)</span></label>
      <input type="number" bind:value={form.max_uses} class="input input-bordered input-glass" min="0" />
    </div>
    <div class="flex gap-3 justify-end pt-2">
      <button class="btn btn-ghost" onclick={() => showModal = false}>Отмена</button>
      <button class="btn btn-primary btn-glow" onclick={handleSave}>Создать</button>
    </div>
  </div>
</Modal>

<ConfirmDialog
  bind:show={showDelete}
  title="Удалить промокод?"
  message={`Промокод «${editing?.code}» будет удалён безвозвратно.`}
  onConfirm={handleDelete}
  onCancel={() => showDelete = false} />
