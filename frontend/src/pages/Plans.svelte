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

  let plans = $state([]);
  let loading = $state(true);
  let showModal = $state(false);
  let editPlan = $state(null);
  let confirmDelete = $state(false);
  let deleteTarget = $state(null);
  let search = $state('');

  let filteredPlans = $derived(
    search
      ? plans.filter(p =>
          p.name.toLowerCase().includes(search.toLowerCase()) ||
          String(p.price).includes(search)
        )
      : plans
  );

  let form = $state({ name: '', description: '', price: 0, duration_days: 30, is_active: true });

  async function loadPlans() {
    loading = true;
    try { plans = await api.getPlans({ limit: 100 }); }
    catch (e) { toasts.error('Ошибка загрузки тарифов: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadPlans);

  function openCreate() {
    editPlan = null;
    form = { name: '', description: '', price: 0, duration_days: 30, is_active: true };
    showModal = true;
  }
  function openEdit(plan) {
    editPlan = plan;
    form = { name: plan.name || '', description: plan.description || '', price: plan.price || 0, duration_days: plan.duration_days || 30, is_active: plan.is_active !== false };
    showModal = true;
  }

  async function savePlan() {
    if (!form.name?.trim()) return toasts.error('Введите название тарифа');
    if (form.price < 0) return toasts.error('Цена не может быть отрицательной');
    if (form.duration_days < 1) return tosts.error('Дней должно быть не менее 1');
    try {
      if (editPlan) {
        await api.updatePlan(editPlan.id, form);
        toasts.success('Тариф обновлён');
      } else {
        const translit = { 'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya' };
        const slug = form.name.toLowerCase().replace(/[а-яё]/g, c => translit[c] || '').replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 64) || ('plan_' + Date.now());
        await api.createPlan({ ...form, slug });
        toasts.success('Тариф создан');
      }
      showModal = false; await loadPlans();
    } catch (e) { toasts.error(e.message); }
  }

  function askDelete(plan) { deleteTarget = plan; confirmDelete = true; }
  async function doDelete() {
    if (!deleteTarget) return;
    try { await api.deletePlan(deleteTarget.id); toasts.success('Тариф удалён'); await loadPlans(); }
    catch (e) { toasts.error(e.message); }
    confirmDelete = false; deleteTarget = null;
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true, render: (r) => `<span class="text-[11px] text-muted">${r.id}</span>` },
    { key: 'name', label: 'Название', sortable: true, render: (r) => `<span class="font-medium text-[12px]">${r.name}</span>` },
    { key: 'slug', label: 'Slug', sortable: true, render: (r) => `<span class="font-mono text-[11px] text-muted">${r.slug}</span>` },
    { key: 'duration_days', label: 'Дней', sortable: true },
    { key: 'price', label: 'Цена', sortable: true, render: (r) => `<span class="font-mono text-[11px]">${formatPrice(r.price)}</span>` },
    { key: 'currency', label: 'Валюта', sortable: false },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Тарифы</h1>
      <p class="text-sm text-muted mt-1">{plans.length} тарифов</p>
    </div>
    <button class="btn btn-primary" onclick={openCreate}><Icon name="plus" class="w-4 h-4" /> Новый тариф</button>
    <input type="text" bind:value={search} placeholder="Поиск..." class="input w-full sm:w-60" />
  </div>

  <Table columns={columns} data={filteredPlans}>
    {#snippet actions(row)}
      <span class="badge text-[10px] {row.is_active !== false ? 'badge-success' : 'badge-danger'}">{row.is_active !== false ? 'Активен' : 'Неактивен'}</span>
      <button class="btn btn-ghost btn-xs text-muted hover:text-zinc-300" onclick={() => openEdit(row)}><Icon name="pencil" class="w-3 h-3" /></button>
      <button class="btn btn-ghost btn-xs text-danger hover:text-danger-hover" onclick={() => askDelete(row)}><Icon name="trash-2" class="w-3 h-3" /></button>
    {/snippet}
  </Table>
</div>

<Modal bind:open={showModal} title={editPlan ? 'Редактировать тариф' : 'Новый тариф'}>
  <form class="space-y-4" onsubmit={(e) => { e.preventDefault(); savePlan(); }}>
    <div class="space-y-1">
      <label class="label"><span class="label-text">Название</span></label>
      <input type="text" bind:value={form.name} class="input w-full" placeholder="Название тарифа" required />
    </div>
    <div class="space-y-1">
      <label class="label"><span class="label-text">Описание</span></label>
      <textarea bind:value={form.description} class="textarea w-full h-20" placeholder="Описание тарифа"></textarea>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div class="space-y-1">
        <label class="label"><span class="label-text">Цена (₽)</span></label>
        <input type="number" bind:value={form.price} class="input w-full" min="0" required />
      </div>
      <div class="space-y-1">
        <label class="label"><span class="label-text">Дней</span></label>
        <input type="number" bind:value={form.duration_days} class="input w-full" min="1" required />
      </div>
    </div>
    <div>
      <label class="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" bind:checked={form.is_active} class="w-4 h-4 rounded accent-accent" />
        <span class="text-sm">Активен</span>
      </label>
    </div>
    <div class="flex gap-3 pt-2">
      <button type="button" class="btn btn-secondary flex-1" onclick={() => showModal = false}>Отмена</button>
      <button type="submit" class="btn btn-primary flex-1">{editPlan ? 'Сохранить' : 'Создать'}</button>
    </div>
  </form>
</Modal>

<ConfirmDialog bind:show={confirmDelete} title="Удалить тариф?" message={`Удалить тариф «${deleteTarget?.name}»?`} confirmText="Удалить" danger onConfirm={doDelete} />
