<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import { formatPrice } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import Modal from '../components/Modal.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';
  import Spinner from '../components/Spinner.svelte';

  let plans = $state([]);
  let loading = $state(true);
  let showModal = $state(false);
  let editing = $state(null);
  let showDelete = $state(false);
  let form = $state({ name: '', slug: '', duration_days: 30, price: 0, currency: 'RUB', description: '', sort_order: 0 });

  async function loadPlans() {
    loading = true;
    try {
      plans = await api.getPlans();
    } catch (e) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  onMount(loadPlans);

  function openCreate() {
    editing = null;
    form = { name: '', slug: '', duration_days: 30, price: 0, currency: 'RUB', description: '', sort_order: 0 };
    showModal = true;
  }

  function openEdit(plan) {
    editing = plan;
    form = { name: plan.name, slug: plan.slug, duration_days: plan.duration_days, price: plan.price, currency: plan.currency, description: plan.description || '', sort_order: plan.sort_order || 0 };
    showModal = true;
  }

  async function handleSave() {
    try {
      if (editing) {
        await api.updatePlan(editing.id, form);
        toasts.success('Тариф обновлён');
      } else {
        await api.createPlan(form);
        toasts.success('Тариф создан');
      }
      showModal = false;
      await loadPlans();
    } catch (e) {
      toasts.error(e.message);
    }
  }

  async function handleToggle(plan) {
    try {
      await api.togglePlan(plan.id);
      toasts.success('Статус изменён');
      await loadPlans();
    } catch (e) {
      toasts.error(e.message);
    }
  }

  async function handleDelete() {
    if (!editing) return;
    try {
      await api.deletePlan(editing.id);
      toasts.success('Тариф удалён');
      showDelete = false;
      await loadPlans();
    } catch (e) {
      toasts.error(e.message);
    }
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'name', label: 'Название', sortable: true, render: (r) => `<span class="font-medium">${r.name}</span>` },
    { key: 'slug', label: 'Slug', render: (r) => `<span class="text-xs text-base-content/50">${r.slug}</span>` },
    { key: 'duration_days', label: 'Дней', sortable: true, render: (r) => `<span class="text-base-content/60">${r.duration_days} дн.</span>` },
    { key: 'price', label: 'Цена', sortable: true, render: (r) => `<span class="font-medium text-primary">${formatPrice(r.price, r.currency)}</span>` },
    { key: 'currency', label: 'Валюта' },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-bold">Тарифы</h1>
      <p class="text-sm text-base-content/40 mt-1">{plans.length} тарифов</p>
    </div>
    <button onclick={openCreate} class="btn btn-primary btn-sm btn-glow gap-2">
      Создать
    </button>
  </div>

  <Table columns={columns} data={plans}>
    {#snippet actions(row)}
      <div class="flex items-center gap-2">
        <span class="badge badge-sm badge-glow {row.is_active ? 'badge-success' : 'badge-ghost'}">
          {row.is_active ? 'Активен' : 'Выкл'}
        </span>
        <div class="dropdown dropdown-end">
          <button tabindex="0" class="btn btn-xs btn-ghost btn-circle">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" /></svg>
          </button>
          <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow-lg bg-base-200 rounded-xl w-40 border border-base-300/50">
            <li><button onclick={() => handleToggle(row)}>{row.is_active ? 'Выключить' : 'Включить'}</button></li>
            <li><button onclick={() => openEdit(row)}>Редактировать</button></li>
            <li><button class="text-error" onclick={() => { editing = row; showDelete = true; }}>Удалить</button></li>
          </ul>
        </div>
      </div>
    {/snippet}
  </Table>
</div>

<Modal bind:open={showModal} title={editing ? 'Редактировать тариф' : 'Новый тариф'} size="md">
  <div class="space-y-4">
    <div class="form-control">
      <label class="label"><span class="label-text text-xs font-medium">Название</span></label>
      <input type="text" bind:value={form.name} class="input input-bordered input-glass" placeholder="30 дней" />
    </div>
    <div class="form-control">
      <label class="label"><span class="label-text text-xs font-medium">Slug</span></label>
      <input type="text" bind:value={form.slug} class="input input-bordered input-glass" placeholder="30_days" disabled={!!editing} />
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div class="form-control">
        <label class="label"><span class="label-text text-xs font-medium">Дней</span></label>
        <input type="number" bind:value={form.duration_days} class="input input-bordered input-glass" min="1" />
      </div>
      <div class="form-control">
        <label class="label"><span class="label-text text-xs font-medium">Цена</span></label>
        <input type="number" bind:value={form.price} class="input input-bordered input-glass" min="0" />
      </div>
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div class="form-control">
        <label class="label"><span class="label-text text-xs font-medium">Валюта</span></label>
        <input type="text" bind:value={form.currency} class="input input-bordered input-glass" />
      </div>
      <div class="form-control">
        <label class="label"><span class="label-text text-xs font-medium">Порядок</span></label>
        <input type="number" bind:value={form.sort_order} class="input input-bordered input-glass" />
      </div>
    </div>
    <div class="form-control">
      <label class="label"><span class="label-text text-xs font-medium">Описание</span></label>
      <textarea bind:value={form.description} class="textarea textarea-bordered input-glass h-20" placeholder="Описание тарифа..."></textarea>
    </div>
    <div class="flex gap-3 justify-end pt-2">
      <button class="btn btn-ghost" onclick={() => showModal = false}>Отмена</button>
      <button class="btn btn-primary btn-glow" onclick={handleSave}>{editing ? 'Сохранить' : 'Создать'}</button>
    </div>
  </div>
</Modal>

<ConfirmDialog
  bind:show={showDelete}
  title="Удалить тариф?"
  message={`Тариф «${editing?.name}» будет удалён безвозвратно.`}
  confirmText="Удалить"
  confirmClass="btn-error"
  onConfirm={handleDelete}
  onCancel={() => showDelete = false} />
