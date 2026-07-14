<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import Table from '../components/Table.svelte';
  import Modal from '../components/Modal.svelte';
  import Spinner from '../components/Spinner.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';

  let promos = $state([]);
  let loading = $state(true);
  let showModal = $state(false);
  let showConfirm = $state(false);
  let pendingAction = $state(null);

  let form = $state({
    code: '', promo_type: 'percent', value: 0, max_uses: 0, plan_id: null,
  });

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'code', label: 'Код', sortable: true },
    { key: 'promo_type', label: 'Тип' },
    { key: 'value', label: 'Значение' },
    { key: 'max_uses', label: 'Макс. использований' },
    { key: 'used_count', label: 'Использовано' },
    { key: 'is_active', label: 'Статус' },
  ];

  onMount(loadPromos);

  async function loadPromos() {
    loading = true;
    try {
      promos = await api.getPromos();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    } finally {
      loading = false;
    }
  }

  async function handleCreate() {
    try {
      await api.createPromo(form);
      toasts.success('Промокод создан');
      showModal = false;
      await loadPromos();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  async function handleToggle(promo) {
    try {
      await api.togglePromo(promo.id);
      toasts.success('Статус изменён');
      await loadPromos();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  function confirmDelete(promo) {
    pendingAction = async () => {
      try {
        await api.deletePromo(promo.id);
        toasts.success('Промокод удалён');
        await loadPromos();
      } catch (e) {
        toasts.error('Ошибка: ' + e.message);
      }
    };
    showConfirm = true;
  }
</script>

<div class="fade-in">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">Промокоды</h1>
    <button class="btn btn-sm btn-primary" onclick={() => showModal = true}>+ Создать</button>
  </div>

  <Spinner {loading} />

  {#if !loading}
    <Table {columns} data={promos}>
      {#snippet actions(row)}
        <div class="flex gap-1 items-center">
          <span class="badge badge-sm" class:badge-success={row.is_active} class:badge-ghost={!row.is_active}>
            {row.is_active ? 'Активен' : 'Выкл'}
          </span>
          <button class="btn btn-xs btn-ghost" onclick={() => handleToggle(row)}>Перекл.</button>
          <button class="btn btn-xs btn-error btn-ghost" onclick={() => confirmDelete(row)}>🗑</button>
        </div>
      {/snippet}
    </Table>
  {/if}
</div>

<Modal bind:open={showModal} title="Новый промокод" size="md">
  <div class="space-y-4">
    <div class="form-control">
      <label class="label"><span class="label-text">Код</span></label>
      <input type="text" bind:value={form.code} class="input input-bordered" placeholder="SUMMER2024" />
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div class="form-control">
        <label class="label"><span class="label-text">Тип</span></label>
        <select bind:value={form.promo_type} class="select select-bordered">
          <option value="percent">Процент</option>
          <option value="fixed">Фиксированная сумма</option>
          <option value="days">Дни</option>
        </select>
      </div>
      <div class="form-control">
        <label class="label"><span class="label-text">Значение</span></label>
        <input type="number" bind:value={form.value} class="input input-bordered" />
      </div>
    </div>
    <div class="form-control">
      <label class="label"><span class="label-text">Макс. использований (0 = безлимит)</span></label>
      <input type="number" bind:value={form.max_uses} class="input input-bordered" />
    </div>
    <div class="flex justify-end gap-2 mt-4">
      <button class="btn btn-ghost" onclick={() => showModal = false}>Отмена</button>
      <button class="btn btn-primary" onclick={handleCreate}>Создать</button>
    </div>
  </div>
</Modal>

<ConfirmDialog bind:show={showConfirm} onConfirm={pendingAction} title="Удалить промокод?" message="Это действие необратимо." />
