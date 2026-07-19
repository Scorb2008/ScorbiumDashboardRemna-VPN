<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDateTime } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import Spinner from '../components/Spinner.svelte';
  import Modal from '../components/Modal.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';
  import Icon from '../components/Icon.svelte';

  let admins = $state([]);
  let currentAdmin = $state(null);
  let loading = $state(true);

  let showCreateModal = $state(false);
  let createForm = $state({ username: '', password: '', role: 'operator' });

  let showEditModal = $state(false);
  let editTarget = $state(null);
  let editForm = $state({ username: '', password: '', role: 'operator', is_active: true });

  let confirmDelete = $state(false);
  let deleteTarget = $state(null);

  async function loadAdmins() {
    loading = true;
    try {
      const [a, me] = await Promise.all([
        api.getAdmins(),
        api.getCurrentAdmin(),
      ]);
      admins = a;
      currentAdmin = me;
    } catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadAdmins);

  function openCreate() {
    createForm = { username: '', password: '', role: 'operator' };
    showCreateModal = true;
  }

  async function handleCreate() {
    if (!createForm.username || !createForm.password) {
      toasts.error('Заполните все поля');
      return;
    }
    if (createForm.password.length < 8) {
      toasts.error('Пароль должен быть не менее 8 символов');
      return;
    }
    try {
      await api.createAdmin(createForm);
      toasts.success('Администратор создан');
      showCreateModal = false;
      await loadAdmins();
    } catch (e) { toasts.error(e.message); }
  }

  function openEdit(admin) {
    editTarget = admin;
    editForm = { username: admin.username, password: '', role: admin.role, is_active: admin.is_active };
    showEditModal = true;
  }

  async function handleEdit() {
    if (!editTarget) return;
    if (!editForm.username?.trim()) return toasts.error('Введите имя пользователя');
    if (editForm.password && editForm.password.length < 8) return toasts.error('Пароль должен быть не менее 8 символов');
    try {
      const data = { username: editForm.username, role: editForm.role, is_active: editForm.is_active };
      if (editForm.password) data.password = editForm.password;
      await api.updateAdmin(editTarget.id, data);
      toasts.success('Администратор обновлён');
      showEditModal = false;
      await loadAdmins();
    } catch (e) { toasts.error(e.message); }
  }

  function askDelete(admin) {
    if (admin.username === currentAdmin?.username) {
      toasts.error('Нельзя удалить самого себя');
      return;
    }
    deleteTarget = admin;
    confirmDelete = true;
  }

  async function doDelete() {
    if (!deleteTarget) return;
    try {
      await api.deleteAdmin(deleteTarget.id);
      toasts.success('Администратор удалён');
      await loadAdmins();
    } catch (e) { toasts.error(e.message); }
    confirmDelete = false; deleteTarget = null;
  }

  function roleBadge(role) {
    switch (role) {
      case 'superadmin': return 'badge-accent';
      case 'manager': return 'badge-warning';
      case 'operator': return 'badge-neutral';
      default: return '';
    }
  }

  function roleText(role) {
    switch (role) {
      case 'superadmin': return 'СуперАдмин';
      case 'manager': return 'Менеджер';
      case 'operator': return 'Оператор';
      default: return role;
    }
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true, render: (r) => `<span class="font-mono text-xs text-muted">${r.id}</span>` },
    { key: 'username', label: 'Username', sortable: true, render: (r) => `<span class="font-medium text-[13px]">${r.username}${r.username === currentAdmin?.username ? ' <span class="text-muted text-xs">(вы)</span>' : ''}</span>` },
    { key: 'role', label: 'Роль', sortable: true, render: (r) => `<span class="badge ${roleBadge(r.role)}">${roleText(r.role)}</span>` },
    { key: 'is_active', label: 'Статус', sortable: true, render: (r) => `<span class="badge ${r.is_active !== false ? 'badge-success' : 'badge-danger'}">${r.is_active !== false ? 'Активен' : 'Блокирован'}</span>` },
    { key: 'has_2fa', label: '2FA', sortable: true, render: (r) => r.has_2fa ? '<span class="badge badge-accent">✓</span>' : '<span class="text-muted text-xs">—</span>' },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight text-text">Администраторы</h1>
      <p class="text-sm text-muted mt-1">{admins.length} администраторов</p>
    </div>
    <button class="btn btn-primary" onclick={openCreate}>
      <Icon name="plus" class="w-4 h-4" />
      Новый администратор
    </button>
  </div>

  {#if admins.length > 0}
    <Table columns={columns} data={admins}>
      {#snippet actions(row)}
        <button class="btn btn-ghost btn-sm text-muted hover:text-text" onclick={() => openEdit(row)} title="Редактировать">
          <Icon name="pencil" class="w-3.5 h-3.5" />
        </button>
        <button class="btn btn-ghost btn-sm text-muted hover:text-danger" onclick={() => askDelete(row)} title="Удалить" disabled={row.username === currentAdmin?.username}>
          <Icon name="trash-2" class="w-3.5 h-3.5" />
        </button>
      {/snippet}
    </Table>
  {:else if !loading}
    <div class="card p-10 flex flex-col items-center gap-3 text-center">
      <Icon name="shield" class="w-10 h-10 text-muted" />
      <p class="text-[15px] font-medium">Нет администраторов</p>
    </div>
  {/if}
</div>

<Modal bind:open={showCreateModal} title="Новый администратор">
  <form class="space-y-3.5" onsubmit={(e) => { e.preventDefault(); handleCreate(); }}>
    <div class="space-y-1">
      <label class="label">Username</label>
      <input type="text" bind:value={createForm.username} class="input w-full" placeholder="admin" required />
    </div>
    <div class="space-y-1">
      <label class="label">Пароль</label>
      <input type="password" bind:value={createForm.password} class="input w-full" placeholder="Минимум 6 символов" required />
    </div>
    <div class="space-y-1">
      <label class="label">Роль</label>
      <select bind:value={createForm.role} class="select w-full">
        <option value="superadmin">СуперАдмин</option>
        <option value="manager">Менеджер</option>
        <option value="operator">Оператор</option>
      </select>
    </div>
    <div class="flex gap-3 pt-1">
      <button type="button" class="btn btn-secondary flex-1" onclick={() => showCreateModal = false}>Отмена</button>
      <button type="submit" class="btn btn-primary flex-1">Создать</button>
    </div>
  </form>
</Modal>

<Modal bind:open={showEditModal} title="Редактировать администратора">
  <form class="space-y-3.5" onsubmit={(e) => { e.preventDefault(); handleEdit(); }}>
    <div class="space-y-1">
      <label class="label">Username</label>
      <input type="text" bind:value={editForm.username} class="input w-full" required />
    </div>
    <div class="space-y-1">
      <label class="label">Новый пароль (оставьте пустым, чтобы не менять)</label>
      <input type="password" bind:value={editForm.password} class="input w-full" placeholder="Оставьте пустым" />
    </div>
    <div class="space-y-1">
      <label class="label">Роль</label>
      <select bind:value={editForm.role} class="select w-full">
        <option value="superadmin">СуперАдмин</option>
        <option value="manager">Менеджер</option>
        <option value="operator">Оператор</option>
      </select>
    </div>
    <label class="flex items-center gap-2.5 cursor-pointer py-1">
      <input type="checkbox" bind:checked={editForm.is_active} class="w-4 h-4 rounded accent-accent" />
      <span class="text-[13px]">Активен</span>
    </label>
    <div class="flex gap-3 pt-1">
      <button type="button" class="btn btn-secondary flex-1" onclick={() => showEditModal = false}>Отмена</button>
      <button type="submit" class="btn btn-primary flex-1">Сохранить</button>
    </div>
  </form>
</Modal>

<ConfirmDialog
  bind:show={confirmDelete}
  title="Удалить администратора?"
  message={`Удалить ${deleteTarget?.username}? Это действие необратимо.`}
  confirmText="Удалить" danger
  onConfirm={doDelete} />
