<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
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

  let showSetup2FA = $state(false);
  let setup2FALoading = $state(false);
  let setup2FAResult = $state(null);
  let verify2FACode = $state('');
  let verify2FALoading = $state(false);

  let showDisable2FA = $state(false);
  let disable2FAPassword = $state('');
  let disable2FALoading = $state(false);

  let confirmDisable2FA = $state(false);
  let disable2FATarget = $state(null);

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

  async function openSetup2FA() {
    setup2FALoading = true;
    showSetup2FA = true;
    setup2FAResult = null;
    verify2FACode = '';
    try {
      setup2FAResult = await api.setup2fa();
      await loadAdmins();
    } catch (e) {
      toasts.error(e.message);
      showSetup2FA = false;
    } finally {
      setup2FALoading = false;
    }
  }

  async function handleVerify2FA() {
    if (!verify2FACode || verify2FACode.length < 6) return;
    verify2FALoading = true;
    try {
      await api.verify2fa(verify2FACode);
      toasts.success('2FA включена');
      showSetup2FA = false;
      setup2FAResult = null;
      await loadAdmins();
    } catch (e) { toasts.error(e.message); }
    finally { verify2FALoading = false; }
  }

  function askDisable2FA(admin) {
    disable2FATarget = admin;
    disable2FAPassword = '';
    confirmDisable2FA = true;
  }

  async function handleDisable2FA() {
    if (!disable2FAPassword) return;
    disable2FALoading = true;
    try {
      await api.disable2fa(disable2FAPassword);
      toasts.success('2FA отключена');
      confirmDisable2FA = false;
      disable2FATarget = null;
      await loadAdmins();
    } catch (e) { toasts.error(e.message); }
    finally { disable2FALoading = false; }
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
    { key: 'id', label: 'ID', sortable: true, render: (r) => `<span class="font-mono text-[11px] text-muted">${r.id}</span>` },
    { key: 'username', label: 'Username', sortable: true, render: (r) => `<span class="font-medium text-[13px]">${r.username}${r.username === currentAdmin?.username ? ' <span class="text-muted text-[11px]">(вы)</span>' : ''}</span>` },
    { key: 'role', label: 'Роль', sortable: true, render: (r) => `<span class="badge text-[10px] ${roleBadge(r.role)}">${roleText(r.role)}</span>` },
    { key: 'is_active', label: 'Статус', sortable: true, render: (r) => `<span class="badge text-[10px] ${r.is_active !== false ? 'badge-success' : 'badge-danger'}">${r.is_active !== false ? 'Активен' : 'Блокирован'}</span>` },
    { key: 'has_2fa', label: '2FA', sortable: true, render: (r) => r.has_2fa ? '<span class="badge badge-accent text-[10px]">✓</span>' : '<span class="text-muted text-[11px]">—</span>' },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight text-text">Администраторы</h1>
      <p class="text-sm text-muted mt-1">{admins.length} администраторов</p>
    </div>
    <div class="flex gap-2">
      {#if currentAdmin?.role === 'superadmin' && !currentAdmin?.has_2fa}
        <button class="btn btn-secondary" onclick={openSetup2FA}>
          <Icon name="shield" class="w-4 h-4" />
          Включить 2FA
        </button>
      {/if}
      <button class="btn btn-primary" onclick={openCreate}>
        <Icon name="plus" class="w-4 h-4" />
        Новый администратор
      </button>
    </div>
  </div>

  {#if admins.length > 0}
    <Table columns={columns} data={admins}>
      {#snippet actions(row)}
        <button class="btn btn-ghost btn-xs text-muted hover:text-text" onclick={() => openEdit(row)} title="Редактировать">
          <Icon name="pencil" class="w-3 h-3" />
        </button>
        {#if row.has_2fa && row.username === currentAdmin?.username}
          <button class="btn btn-ghost btn-xs text-warning hover:text-warning-hover" onclick={() => askDisable2FA(row)} title="Отключить 2FA">
            <Icon name="shieldOff" class="w-3 h-3" />
          </button>
        {/if}
        <button class="btn btn-ghost btn-xs text-muted hover:text-danger" onclick={() => askDelete(row)} title="Удалить" disabled={row.username === currentAdmin?.username}>
          <Icon name="trash-2" class="w-3 h-3" />
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
      <input type="password" bind:value={createForm.password} class="input w-full" placeholder="Минимум 8 символов" required />
    </div>
    <div class="space-y-1">
      <label class="label">Роль</label>
      <select bind:value={createForm.role} class="select w-full">
        {#if currentAdmin?.role === 'superadmin'}
          <option value="superadmin">СуперАдмин</option>
        {/if}
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
      <select bind:value={editForm.role} class="select w-full" disabled={editTarget?.username === currentAdmin?.username}>
        {#if currentAdmin?.role === 'superadmin'}
          <option value="superadmin">СуперАдмин</option>
        {/if}
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

<Modal bind:open={showSetup2FA} title="Настройка 2FA" size="md">
  {#if setup2FALoading}
    <div class="flex items-center justify-center py-10">
      <div class="w-6 h-6 border-2 border-accent/30 border-t-accent rounded-full animate-spin"></div>
    </div>
  {:else if setup2FAResult}
    <div class="space-y-4">
      <div class="flex flex-col items-center gap-3">
        <img src={setup2FAResult.qr_code} alt="QR Code" class="w-48 h-48 rounded-lg" />
        <div class="text-center">
          <p class="text-[12px] text-muted mb-1">Или введите секрет вручную:</p>
          <code class="text-[14px] font-mono text-accent bg-accent/5 px-3 py-1.5 rounded-lg select-all">{setup2FAResult.secret}</code>
        </div>
      </div>

      <div class="bg-surface-2/50 rounded-lg p-3">
        <p class="text-[12px] text-muted mb-2">Резервные коды (сохраните их):</p>
        <div class="grid grid-cols-2 gap-1">
          {#each setup2FAResult.backup_codes as code}
            <code class="text-[12px] font-mono text-text bg-surface-3/50 px-2 py-1 rounded text-center select-all">{code}</code>
          {/each}
        </div>
      </div>

      <div class="space-y-1">
        <label class="label">Введите код из аутентификатора для подтверждения</label>
        <input type="text" inputmode="numeric" maxlength="6" bind:value={verify2FACode} class="input w-full text-center text-[20px] tracking-[0.5em] font-mono" placeholder="000000" />
      </div>

      <div class="flex gap-3 pt-1">
        <button type="button" class="btn btn-secondary flex-1" onclick={() => { showSetup2FA = false; setup2FAResult = null; }}>Отмена</button>
        <button class="btn btn-primary flex-1" onclick={handleVerify2FA} disabled={verify2FACode.length < 6 || verify2FALoading}>
          {#if verify2FALoading}
            <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
          {:else}
            Подтвердить
          {/if}
        </button>
      </div>
    </div>
  {/if}
</Modal>

<ConfirmDialog
  bind:show={confirmDelete}
  title="Удалить администратора?"
  message={`Удалить ${deleteTarget?.username}? Это действие необратимо.`}
  confirmText="Удалить" danger
  onConfirm={doDelete} />

<ConfirmDialog
  bind:show={confirmDisable2FA}
  title="Отключить 2FA?"
  message="Введите пароль для подтверждения отключения двухфакторной аутентификации."
  confirmText="Отключить" danger
  onConfirm={handleDisable2FA}
  onCancel={() => { confirmDisable2FA = false; disable2FATarget = null; disable2FAPassword = ''; }}
>
  <input type="password" bind:value={disable2FAPassword} class="input w-full mt-3" placeholder="Пароль" />
</ConfirmDialog>
