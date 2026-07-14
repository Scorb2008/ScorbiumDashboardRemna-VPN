<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import Table from '../components/Table.svelte';
  import Modal from '../components/Modal.svelte';
  import Spinner from '../components/Spinner.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';

  let plans = $state([]);
  let loading = $state(true);
  let showModal = $state(false);
  let editingPlan = $state(null);
  let showConfirm = $state(false);
  let pendingAction = $state(null);

  let form = $state({
    name: '', slug: '', duration_days: 30, price: 0,
    description: '', currency: 'RUB', sort_order: 0,
  });

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: 'Название', sortable: true },
    { key: 'slug', label: 'Slug' },
    { key: 'duration_days', label: 'Дней', sortable: true },
    { key: 'price', label: 'Цена', sortable: true },
    { key: 'currency', label: 'Валюта' },
    { key: 'is_active', label: 'Статус' },
  ];

  onMount(loadPlans);

  async function loadPlans() {
    loading = true;
    try {
      plans = await api.getPlans();
    } catch (e) {
      toasts.error('Ошибка загрузки: ' + e.message);
    } finally {
      loading = false;
    }
  }

  function openCreate() {
    editingPlan = null;
    form = { name: '', slug: '', duration_days: 30, price: 0, description: '', currency: 'RUB', sort_order: 0 };
    showModal = true;
  }

  function openEdit(plan) {
    editingPlan = plan;
    form = {
      name: plan.name, slug: plan.slug, duration_days: plan.duration_days,
      price: plan.price, description: plan.description || '',
      currency: plan.currency, sort_order: plan.sort_order || 0,
    };
    showModal = true;
  }

  async function handleSave() {
    try {
      if (editingPlan) {
        await api.updatePlan(editingPlan.id, form);
        toasts.success('Тариф обновлён');
      } else {
        await api.createPlan(form);
        toasts.success('Тариф создан');
      }
      showModal = false;
      await loadPlans();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  async function handleToggle(plan) {
    try {
      await api.togglePlan(plan.id);
      toasts.success('Статус изменён');
      await loadPlans();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  function confirmDelete(plan) {
    pendingAction = async () => {
      try {
        await api.deletePlan(plan.id);
        toasts.success('Тариф удалён');
        await loadPlans();
      } catch (e) {
        toasts.error('Ошибка: ' + e.message);
      }
    };
    showConfirm = true;
  }
</script>

<div class="fade-in">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">Тарифы</h1>
    <button class="btn btn-sm btn-primary" onclick={openCreate}>+ Создать</button>
  </div>

  <Spinner {loading} />

  {#if !loading}
    <Table {columns} data={plans}>
      {#snippet actions(row)}
        <div class="flex gap-1 items-center">
          <span class="badge badge-sm" class:badge-success={row.is_active} class:badge-ghost={!row.is_active}>
            {row.is_active ? 'Активен' : 'Выкл'}
          </span>
          <button class="btn btn-xs btn-ghost" onclick={() => handleToggle(row)}>
            {row.is_active ? 'Выкл' : 'Вкл'}
          </button>
        </div>
      {/snippet}
    </Table>
  {/if}
</div>

<Modal bind:open={showModal} title={editingPlan ? 'Редактировать тариф' : 'Новый тариф'} size="lg">
  <div class="space-y-4">
    <div class="form-control">
      <label class="label"><span class="label-text">Название</span></label>
      <input type="text" bind:value={form.name} class="input input-bordered" />
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div class="form-control">
        <label class="label"><span class="label-text">Slug</span></label>
        <input type="text" bind:value={form.slug} class="input input-bordered" />
      </div>
      <div class="form-control">
        <label class="label"><span class="label-text">Дней</span></label>
        <input type="number" bind:value={form.duration_days} class="input input-bordered" />
      </div>
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div class="form-control">
        <label class="label"><span class="label-text">Цена</span></label>
        <input type="number" bind:value={form.price} class="input input-bordered" />
      </div>
      <div class="form-control">
        <label class="label"><span class="label-text">Валюта</span></label>
        <input type="text" bind:value={form.currency} class="input input-bordered" />
      </div>
    </div>
    <div class="form-control">
      <label class="label"><span class="label-text">Описание</span></label>
      <textarea bind:value={form.description} class="textarea textarea-bordered h-20"></textarea>
    </div>
    <div class="form-control">
      <label class="label"><span class="label-text">Порядок</span></label>
      <input type="number" bind:value={form.sort_order} class="input input-bordered" />
    </div>
    <div class="flex justify-end gap-2 mt-4">
      <button class="btn btn-ghost" onclick={() => showModal = false}>Отмена</button>
      <button class="btn btn-primary" onclick={handleSave}>
        {editingPlan ? 'Сохранить' : 'Создать'}
      </button>
    </div>
  </div>
</Modal>

<ConfirmDialog bind:show={showConfirm} onConfirm={pendingAction} title="Удалить тариф?" message="Это действие необратимо." />
