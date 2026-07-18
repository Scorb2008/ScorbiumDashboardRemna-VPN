<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let loading = $state(true);
  let saving = $state(false);
  let groups = $state([]);
  let selectedIds = $state([]);
  let fetchError = $state('');

  async function loadAll() {
    loading = true;
    fetchError = '';
    try {
      const [groupsData, selectedData] = await Promise.all([
        api.getVpnGroups(),
        api.getSelectedVpnGroups(),
      ]);
      groups = groupsData?.groups || [];
      selectedIds = selectedData?.group_ids || [];
    } catch (e) {
      fetchError = e.message;
      toasts.error('Ошибка загрузки групп: ' + e.message);
    } finally {
      loading = false;
    }
  }

  onMount(loadAll);

  function toggleGroup(gid) {
    if (selectedIds.includes(gid)) {
      selectedIds = selectedIds.filter(id => id !== gid);
    } else {
      selectedIds = [...selectedIds, gid];
    }
  }

  async function saveGroups() {
    saving = true;
    try {
      await api.saveSelectedVpnGroups(selectedIds);
      toasts.success('Группы сохранены');
    } catch (e) {
      toasts.error('Ошибка сохранения: ' + e.message);
    } finally {
      saving = false;
    }
  }
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Группы VPN</h1>
      <p class="text-sm text-muted mt-1">Выберите группы Remnawave для выдачи подписок пользователям</p>
    </div>
    <button onclick={saveGroups} disabled={saving || loading} class="btn btn-primary">
      {#if saving}
        <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
      {:else}
        <Icon name="check" class="w-4 h-4" />
      {/if}
      Сохранить
    </button>
  </div>

  {#if fetchError}
    <div class="card p-5 border-danger/30 bg-danger/5">
      <div class="flex items-center gap-3">
        <Icon name="alertTriangle" class="w-5 h-5 text-danger" />
        <div>
          <p class="text-[14px] font-medium text-danger">Ошибка подключения к Remnawave</p>
          <p class="text-[13px] text-muted mt-0.5">{fetchError}</p>
        </div>
      </div>
      <button onclick={loadAll} class="btn btn-ghost btn-sm mt-3">
        <Icon name="refreshCw" class="w-3.5 h-3.5" /> Повторить
      </button>
    </div>
  {:else if groups.length === 0 && !loading}
    <div class="card p-8 text-center">
      <Icon name="alertTriangle" class="w-10 h-10 text-warning mx-auto mb-3" />
      <p class="text-[15px] font-medium">Группы не найдены</p>
      <p class="text-[13px] text-muted mt-1">В Remnawave не загружены группы. Создайте группы в панели Remnawave.</p>
      <button onclick={loadAll} class="btn btn-ghost btn-sm mt-3">
        <Icon name="refreshCw" class="w-3.5 h-3.5" /> Обновить
      </button>
    </div>
  {:else}
    <div class="card p-5 space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-[15px] font-semibold flex items-center gap-2">
            <Icon name="shield" class="w-4 h-4 text-accent" />
            Доступные группы ({groups.length})
          </h3>
          <p class="text-[13px] text-muted mt-0.5">
            {#if selectedIds.length > 0}
              Выбрано: <span class="text-accent font-medium">{selectedIds.length}</span> из {groups.length}
            {:else}
              Группы не выбраны — будет использована первая группа по умолчанию
            {/if}
          </p>
        </div>
        <button onclick={loadAll} class="btn btn-ghost btn-sm">
          <Icon name="refreshCw" class="w-3.5 h-3.5" />
        </button>
      </div>

      <div class="space-y-1.5">
        {#each groups as g}
          {@const gid = g.id}
          {@const checked = selectedIds.includes(gid)}
          <button
            onclick={() => toggleGroup(gid)}
            class="w-full flex items-center gap-3 p-3 rounded-[10px] border transition-all text-left
              {checked
                ? 'bg-accent/5 border-accent/30 hover:bg-accent/10'
                : 'bg-surface-3/30 border-surface-4/10 hover:bg-surface-3/50'}">
            <div class="w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all
              {checked ? 'bg-accent border-accent' : 'border-surface-4'}">
              {#if checked}
                <Icon name="check" class="w-3 h-3 text-white" />
              {/if}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-[13px] font-medium">{g.name || `Group #${gid}`}</span>
                {#if g.is_disabled}
                  <span class="text-[10px] font-medium px-1.5 py-0.5 rounded bg-danger/20 text-danger">Отключена</span>
                {/if}
                {#if g.total_users !== undefined}
                  <span class="text-[11px] text-muted">{g.total_users} юз.</span>
                {/if}
              </div>
              {#if g.inbound_tags && g.inbound_tags.length > 0}
                <div class="flex flex-wrap gap-1 mt-1">
                  {#each g.inbound_tags as tag}
                    <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-4/30 text-muted">{tag}</span>
                  {/each}
                </div>
              {/if}
            </div>
          </button>
        {/each}
      </div>
    </div>
  {/if}
</div>
