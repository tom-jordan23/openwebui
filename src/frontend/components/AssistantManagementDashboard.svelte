<script>
    // Import blueprint theme
    import '../styles/blueprint-theme.css';
    import '../styles/blueprint-components.css';
    
    import { onMount, createEventDispatcher } from 'svelte';
    import { writable } from 'svelte/store';
    import Icon from '@iconify/svelte';

    const dispatch = createEventDispatcher();

    // Stores
    const assistants = writable([]);
    const selectedAssistant = writable(null);
    const loading = writable(false);
    const error = writable('');
    const activeTab = writable('overview');

    // Data stores
    const analytics = writable({});
    const deployments = writable([]);
    const conversations = writable([]);
    const prompts = writable([]);

    // UI state
    let showCreateModal = false;
    let showDeployModal = false;
    let showDeleteModal = false;
    let showConversationModal = false;
    let assistantToDelete = null;
    let assistantTypes = [];
    let assistantStatuses = [];
    let deploymentEnvironments = [];

    // Form data
    let newAssistant = {
        name: '',
        description: '',
        system_prompt: '',
        model_id: 'gpt-4',
        assistant_type: 'general',
        temperature: 0.7,
        max_tokens: 2000,
        tags: []
    };

    let deploymentForm = {
        environment: 'development',
        deployment_config: {}
    };

    let searchQuery = '';
    let filterType = '';
    let sortBy = 'created_at';
    let sortOrder = 'desc';

    // Computed
    $: filteredAssistants = $assistants.filter(assistant => {
        const matchesSearch = !searchQuery || 
            assistant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            assistant.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            assistant.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
        
        const matchesType = !filterType || assistant.assistant_type === filterType;
        
        return matchesSearch && matchesType;
    }).sort((a, b) => {
        let aVal = a[sortBy];
        let bVal = b[sortBy];
        
        if (sortBy === 'created_at' || sortBy === 'updated_at') {
            aVal = new Date(aVal);
            bVal = new Date(bVal);
        }
        
        if (sortOrder === 'desc') {
            return bVal > aVal ? 1 : -1;
        } else {
            return aVal > bVal ? 1 : -1;
        }
    });

    // API Functions
    async function fetchAssistants() {
        loading.set(true);
        error.set('');
        
        try {
            const response = await fetch('/api/v1/assistants', {
                headers: {
                    'X-User-ID': 'current_user' // In production, this would come from auth
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            assistants.set(data.assistants || []);
        } catch (err) {
            console.error('Error fetching assistants:', err);
            error.set('Failed to load assistants');
        } finally {
            loading.set(false);
        }
    }

    async function fetchAssistantTypes() {
        try {
            const response = await fetch('/api/v1/assistants/types');
            if (response.ok) {
                const data = await response.json();
                assistantTypes = data.types || [];
            }
        } catch (err) {
            console.error('Error fetching assistant types:', err);
        }
    }

    async function fetchAssistantStatuses() {
        try {
            const response = await fetch('/api/v1/assistants/statuses');
            if (response.ok) {
                const data = await response.json();
                assistantStatuses = data.statuses || [];
            }
        } catch (err) {
            console.error('Error fetching assistant statuses:', err);
        }
    }

    async function fetchDeploymentEnvironments() {
        try {
            const response = await fetch('/api/v1/assistants/environments');
            if (response.ok) {
                const data = await response.json();
                deploymentEnvironments = data.environments || [];
            }
        } catch (err) {
            console.error('Error fetching environments:', err);
        }
    }

    async function createAssistant() {
        loading.set(true);
        error.set('');
        
        try {
            const response = await fetch('/api/v1/assistants', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': 'current_user'
                },
                body: JSON.stringify(newAssistant)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to create assistant');
            }
            
            showCreateModal = false;
            newAssistant = {
                name: '',
                description: '',
                system_prompt: '',
                model_id: 'gpt-4',
                assistant_type: 'general',
                temperature: 0.7,
                max_tokens: 2000,
                tags: []
            };
            
            await fetchAssistants();
        } catch (err) {
            console.error('Error creating assistant:', err);
            error.set(err.message);
        } finally {
            loading.set(false);
        }
    }

    async function deleteAssistant(assistantId) {
        loading.set(true);
        error.set('');
        
        try {
            const response = await fetch(`/api/v1/assistants/${assistantId}`, {
                method: 'DELETE',
                headers: {
                    'X-User-ID': 'current_user'
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to delete assistant');
            }
            
            showDeleteModal = false;
            assistantToDelete = null;
            await fetchAssistants();
        } catch (err) {
            console.error('Error deleting assistant:', err);
            error.set(err.message);
        } finally {
            loading.set(false);
        }
    }

    async function deployAssistant(assistantId) {
        loading.set(true);
        error.set('');
        
        try {
            const response = await fetch(`/api/v1/assistants/${assistantId}/deploy`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': 'current_user'
                },
                body: JSON.stringify(deploymentForm)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to deploy assistant');
            }
            
            showDeployModal = false;
            await fetchAssistants();
            if ($selectedAssistant && $selectedAssistant.id === assistantId) {
                await fetchDeploymentStatus($selectedAssistant.id);
            }
        } catch (err) {
            console.error('Error deploying assistant:', err);
            error.set(err.message);
        } finally {
            loading.set(false);
        }
    }

    async function fetchAssistantDetails(assistantId) {
        try {
            const response = await fetch(`/api/v1/assistants/${assistantId}`, {
                headers: {
                    'X-User-ID': 'current_user'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                selectedAssistant.set(data.assistant);
            }
        } catch (err) {
            console.error('Error fetching assistant details:', err);
        }
    }

    async function fetchAnalytics(assistantId) {
        try {
            const response = await fetch(`/api/v1/assistants/${assistantId}/metrics`, {
                headers: {
                    'X-User-ID': 'current_user'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                analytics.set(data.metrics);
            }
        } catch (err) {
            console.error('Error fetching analytics:', err);
        }
    }

    async function fetchDeploymentStatus(assistantId) {
        try {
            const response = await fetch(`/api/v1/assistants/${assistantId}/deployment-status`, {
                headers: {
                    'X-User-ID': 'current_user'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                deployments.set(data.status);
            }
        } catch (err) {
            console.error('Error fetching deployment status:', err);
        }
    }

    async function fetchConversations(assistantId) {
        try {
            const response = await fetch('/api/v1/conversations/active', {
                headers: {
                    'X-User-ID': 'current_user'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                const assistantConversations = data.active_sessions.filter(
                    session => session.assistant_id === assistantId
                );
                conversations.set(assistantConversations);
            }
        } catch (err) {
            console.error('Error fetching conversations:', err);
        }
    }

    async function fetchPrompts(assistantId) {
        try {
            const response = await fetch(`/api/v1/assistants/${assistantId}/prompts`);
            
            if (response.ok) {
                const data = await response.json();
                prompts.set(data.prompts);
            }
        } catch (err) {
            console.error('Error fetching prompts:', err);
        }
    }

    async function startConversation(assistantId) {
        try {
            const response = await fetch('/api/v1/conversations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': 'current_user'
                },
                body: JSON.stringify({ assistant_id: assistantId })
            });
            
            if (response.ok) {
                const data = await response.json();
                showConversationModal = true;
                // In a real app, this would open the conversation interface
            }
        } catch (err) {
            console.error('Error starting conversation:', err);
            error.set('Failed to start conversation');
        }
    }

    function selectAssistant(assistant) {
        selectedAssistant.set(assistant);
        fetchAssistantDetails(assistant.id);
        fetchAnalytics(assistant.id);
        fetchDeploymentStatus(assistant.id);
        fetchConversations(assistant.id);
        fetchPrompts(assistant.id);
        activeTab.set('overview');
    }

    function formatDate(timestamp) {
        return new Date(timestamp).toLocaleDateString();
    }

    function formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }

    function getStatusColor(status) {
        const colors = {
            'active': 'bg-green-100 text-green-800',
            'draft': 'bg-yellow-100 text-yellow-800',
            'inactive': 'bg-gray-100 text-gray-800',
            'archived': 'bg-red-100 text-red-800'
        };
        return colors[status] || colors.draft;
    }

    function getTypeIcon(type) {
        const icons = {
            'general': 'mdi:robot',
            'specialized': 'mdi:cog',
            'conversational': 'mdi:chat',
            'task_oriented': 'mdi:clipboard-list',
            'analytical': 'mdi:chart-line',
            'creative': 'mdi:palette',
            'support': 'mdi:help-circle',
            'educational': 'mdi:school'
        };
        return icons[type] || icons.general;
    }

    // Lifecycle
    onMount(async () => {
        await Promise.all([
            fetchAssistants(),
            fetchAssistantTypes(),
            fetchAssistantStatuses(),
            fetchDeploymentEnvironments()
        ]);
    });
</script>

<div class="min-h-screen bg-gray-50 p-6">
    <!-- Header -->
    <div class="mb-8">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-3xl font-bold text-gray-900">AI Assistant Management</h1>
                <p class="text-gray-600 mt-2">Create, manage, and monitor your AI assistants</p>
            </div>
            <div class="flex space-x-4">
                <button
                    on:click={() => showCreateModal = true}
                    class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
                >
                    <Icon icon="mdi:plus" class="w-5 h-5" />
                    <span>Create Assistant</span>
                </button>
                <button
                    on:click={fetchAssistants}
                    class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 flex items-center space-x-2"
                    disabled={$loading}
                >
                    <Icon icon="mdi:refresh" class="w-5 h-5" />
                    <span>Refresh</span>
                </button>
            </div>
        </div>
    </div>

    <!-- Error Message -->
    {#if $error}
        <div class="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <div class="flex items-center">
                <Icon icon="mdi:alert-circle" class="w-5 h-5 mr-2" />
                <span>{$error}</span>
                <button 
                    on:click={() => error.set('')}
                    class="ml-auto"
                >
                    <Icon icon="mdi:close" class="w-5 h-5" />
                </button>
            </div>
        </div>
    {/if}

    <div class="grid grid-cols-12 gap-6">
        <!-- Assistant List -->
        <div class="col-span-5">
            <div class="bg-white rounded-lg shadow-sm border">
                <!-- Filters and Search -->
                <div class="p-4 border-b">
                    <div class="space-y-4">
                        <div class="relative">
                            <Icon icon="mdi:magnify" class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                            <input
                                type="text"
                                placeholder="Search assistants..."
                                bind:value={searchQuery}
                                class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                        </div>
                        
                        <div class="flex space-x-4">
                            <select bind:value={filterType} class="flex-1 px-3 py-2 border border-gray-300 rounded-lg">
                                <option value="">All Types</option>
                                {#each assistantTypes as type}
                                    <option value={type.value}>{type.name}</option>
                                {/each}
                            </select>
                            
                            <select bind:value={sortBy} class="px-3 py-2 border border-gray-300 rounded-lg">
                                <option value="created_at">Created</option>
                                <option value="updated_at">Updated</option>
                                <option value="name">Name</option>
                                <option value="user_satisfaction_rating">Rating</option>
                                <option value="total_conversations">Usage</option>
                            </select>
                            
                            <button
                                on:click={() => sortOrder = sortOrder === 'desc' ? 'asc' : 'desc'}
                                class="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                            >
                                <Icon icon={sortOrder === 'desc' ? 'mdi:arrow-down' : 'mdi:arrow-up'} class="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Assistant Cards -->
                <div class="divide-y max-h-[600px] overflow-y-auto">
                    {#if $loading}
                        <div class="p-8 text-center">
                            <Icon icon="mdi:loading" class="w-8 h-8 animate-spin mx-auto text-gray-400" />
                            <p class="text-gray-500 mt-2">Loading assistants...</p>
                        </div>
                    {:else if filteredAssistants.length === 0}
                        <div class="p-8 text-center">
                            <Icon icon="mdi:robot-outline" class="w-12 h-12 mx-auto text-gray-300 mb-4" />
                            <p class="text-gray-500">No assistants found</p>
                            {#if searchQuery || filterType}
                                <button
                                    on:click={() => { searchQuery = ''; filterType = ''; }}
                                    class="text-blue-600 hover:underline mt-2"
                                >
                                    Clear filters
                                </button>
                            {/if}
                        </div>
                    {:else}
                        {#each filteredAssistants as assistant (assistant.id)}
                            <div 
                                class="p-4 cursor-pointer hover:bg-gray-50 {$selectedAssistant?.id === assistant.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''}"
                                on:click={() => selectAssistant(assistant)}
                            >
                                <div class="flex items-start justify-between">
                                    <div class="flex items-start space-x-3 flex-1">
                                        <div class="bg-gray-100 p-2 rounded-lg">
                                            <Icon icon={getTypeIcon(assistant.assistant_type)} class="w-6 h-6 text-gray-600" />
                                        </div>
                                        
                                        <div class="flex-1 min-w-0">
                                            <h3 class="font-medium text-gray-900 truncate">{assistant.name}</h3>
                                            <p class="text-sm text-gray-500 mt-1 line-clamp-2">{assistant.description || 'No description'}</p>
                                            
                                            <div class="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                                                <span>{formatNumber(assistant.total_conversations)} conversations</span>
                                                {#if assistant.user_satisfaction_rating > 0}
                                                    <div class="flex items-center">
                                                        <Icon icon="mdi:star" class="w-3 h-3 text-yellow-400 mr-1" />
                                                        <span>{assistant.user_satisfaction_rating.toFixed(1)}</span>
                                                    </div>
                                                {/if}
                                            </div>
                                            
                                            <div class="flex items-center space-x-2 mt-2">
                                                <span class="px-2 py-1 text-xs rounded-full {getStatusColor(assistant.status)}">
                                                    {assistant.status}
                                                </span>
                                                {#each (assistant.tags || []).slice(0, 2) as tag}
                                                    <span class="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                                                        {tag}
                                                    </span>
                                                {/each}
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="flex flex-col space-y-1">
                                        <button
                                            on:click|stopPropagation={() => startConversation(assistant.id)}
                                            class="p-1 text-gray-400 hover:text-blue-600"
                                            title="Start Conversation"
                                        >
                                            <Icon icon="mdi:chat" class="w-4 h-4" />
                                        </button>
                                        <button
                                            on:click|stopPropagation={() => { selectedAssistant.set(assistant); showDeployModal = true; }}
                                            class="p-1 text-gray-400 hover:text-green-600"
                                            title="Deploy"
                                        >
                                            <Icon icon="mdi:rocket" class="w-4 h-4" />
                                        </button>
                                        <button
                                            on:click|stopPropagation={() => { assistantToDelete = assistant; showDeleteModal = true; }}
                                            class="p-1 text-gray-400 hover:text-red-600"
                                            title="Delete"
                                        >
                                            <Icon icon="mdi:delete" class="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        {/each}
                    {/if}
                </div>
            </div>
        </div>

        <!-- Assistant Details -->
        <div class="col-span-7">
            {#if $selectedAssistant}
                <div class="bg-white rounded-lg shadow-sm border">
                    <!-- Header -->
                    <div class="p-6 border-b">
                        <div class="flex items-center justify-between">
                            <div>
                                <h2 class="text-2xl font-bold text-gray-900">{$selectedAssistant.name}</h2>
                                <p class="text-gray-600 mt-1">{$selectedAssistant.description}</p>
                            </div>
                            <div class="flex space-x-2">
                                <span class="px-3 py-1 text-sm rounded-full {getStatusColor($selectedAssistant.status)}">
                                    {$selectedAssistant.status}
                                </span>
                                <span class="px-3 py-1 text-sm bg-gray-100 text-gray-800 rounded-full">
                                    {$selectedAssistant.assistant_type.replace('_', ' ')}
                                </span>
                            </div>
                        </div>
                        
                        <!-- Quick Stats -->
                        <div class="grid grid-cols-4 gap-4 mt-6">
                            <div class="text-center">
                                <div class="text-2xl font-bold text-gray-900">{formatNumber($selectedAssistant.total_conversations)}</div>
                                <div class="text-sm text-gray-500">Conversations</div>
                            </div>
                            <div class="text-center">
                                <div class="text-2xl font-bold text-gray-900">{$selectedAssistant.user_satisfaction_rating.toFixed(1)}</div>
                                <div class="text-sm text-gray-500">Rating</div>
                            </div>
                            <div class="text-center">
                                <div class="text-2xl font-bold text-gray-900">{$selectedAssistant.avg_response_time.toFixed(1)}s</div>
                                <div class="text-sm text-gray-500">Avg Response</div>
                            </div>
                            <div class="text-center">
                                <div class="text-2xl font-bold text-gray-900">{$selectedAssistant.version}</div>
                                <div class="text-sm text-gray-500">Version</div>
                            </div>
                        </div>
                    </div>

                    <!-- Tabs -->
                    <div class="border-b">
                        <nav class="flex space-x-8 px-6">
                            {#each ['overview', 'analytics', 'deployments', 'conversations', 'prompts'] as tab}
                                <button
                                    on:click={() => activeTab.set(tab)}
                                    class="py-4 px-1 border-b-2 font-medium text-sm {$activeTab === tab ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
                                >
                                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                                </button>
                            {/each}
                        </nav>
                    </div>

                    <!-- Tab Content -->
                    <div class="p-6">
                        {#if $activeTab === 'overview'}
                            <!-- Overview Tab -->
                            <div class="space-y-6">
                                <div class="grid grid-cols-2 gap-6">
                                    <div>
                                        <h3 class="text-lg font-medium text-gray-900 mb-3">Configuration</h3>
                                        <dl class="space-y-2">
                                            <div class="flex justify-between">
                                                <dt class="text-sm text-gray-500">Model ID:</dt>
                                                <dd class="text-sm text-gray-900">{$selectedAssistant.model_id}</dd>
                                            </div>
                                            <div class="flex justify-between">
                                                <dt class="text-sm text-gray-500">Temperature:</dt>
                                                <dd class="text-sm text-gray-900">{$selectedAssistant.temperature}</dd>
                                            </div>
                                            <div class="flex justify-between">
                                                <dt class="text-sm text-gray-500">Max Tokens:</dt>
                                                <dd class="text-sm text-gray-900">{$selectedAssistant.max_tokens}</dd>
                                            </div>
                                            <div class="flex justify-between">
                                                <dt class="text-sm text-gray-500">Context Size:</dt>
                                                <dd class="text-sm text-gray-900">{$selectedAssistant.context_memory_size}</dd>
                                            </div>
                                        </dl>
                                    </div>
                                    
                                    <div>
                                        <h3 class="text-lg font-medium text-gray-900 mb-3">Metadata</h3>
                                        <dl class="space-y-2">
                                            <div class="flex justify-between">
                                                <dt class="text-sm text-gray-500">Created:</dt>
                                                <dd class="text-sm text-gray-900">{formatDate($selectedAssistant.created_at)}</dd>
                                            </div>
                                            <div class="flex justify-between">
                                                <dt class="text-sm text-gray-500">Updated:</dt>
                                                <dd class="text-sm text-gray-900">{formatDate($selectedAssistant.updated_at)}</dd>
                                            </div>
                                            <div class="flex justify-between">
                                                <dt class="text-sm text-gray-500">Primary Prompt:</dt>
                                                <dd class="text-sm text-gray-900">{$selectedAssistant.primary_prompt_id || 'None'}</dd>
                                            </div>
                                        </dl>
                                        
                                        {#if $selectedAssistant.tags && $selectedAssistant.tags.length > 0}
                                            <div class="mt-4">
                                                <h4 class="text-sm font-medium text-gray-700 mb-2">Tags</h4>
                                                <div class="flex flex-wrap gap-1">
                                                    {#each $selectedAssistant.tags as tag}
                                                        <span class="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                                                            {tag}
                                                        </span>
                                                    {/each}
                                                </div>
                                            </div>
                                        {/if}
                                    </div>
                                </div>
                                
                                {#if $selectedAssistant.system_prompt}
                                    <div>
                                        <h3 class="text-lg font-medium text-gray-900 mb-3">System Prompt</h3>
                                        <div class="bg-gray-50 p-4 rounded-lg">
                                            <pre class="text-sm text-gray-800 whitespace-pre-wrap">{$selectedAssistant.system_prompt}</pre>
                                        </div>
                                    </div>
                                {/if}
                            </div>
                        
                        {:else if $activeTab === 'analytics'}
                            <!-- Analytics Tab -->
                            <div class="space-y-6">
                                {#if Object.keys($analytics).length > 0}
                                    <div class="grid grid-cols-3 gap-6">
                                        <div class="bg-blue-50 p-4 rounded-lg">
                                            <h4 class="font-medium text-blue-900">Performance Score</h4>
                                            <div class="text-2xl font-bold text-blue-700 mt-2">
                                                {$analytics.basic_stats?.user_satisfaction_rating?.toFixed(1) || 'N/A'}
                                            </div>
                                        </div>
                                        
                                        <div class="bg-green-50 p-4 rounded-lg">
                                            <h4 class="font-medium text-green-900">Usage Trend</h4>
                                            <div class="text-2xl font-bold text-green-700 mt-2">
                                                {#if $analytics.trends?.conversation_length?.direction === 'up'}
                                                    <Icon icon="mdi:trending-up" class="w-8 h-8 inline" />
                                                {:else if $analytics.trends?.conversation_length?.direction === 'down'}
                                                    <Icon icon="mdi:trending-down" class="w-8 h-8 inline" />
                                                {:else}
                                                    <Icon icon="mdi:trending-neutral" class="w-8 h-8 inline" />
                                                {/if}
                                            </div>
                                        </div>
                                        
                                        <div class="bg-purple-50 p-4 rounded-lg">
                                            <h4 class="font-medium text-purple-900">Active Sessions</h4>
                                            <div class="text-2xl font-bold text-purple-700 mt-2">
                                                {$conversations.length}
                                            </div>
                                        </div>
                                    </div>
                                    
                                    {#if $analytics.detailed_metrics}
                                        <div>
                                            <h3 class="text-lg font-medium text-gray-900 mb-4">Detailed Metrics</h3>
                                            <div class="grid grid-cols-2 gap-4">
                                                {#each Object.entries($analytics.detailed_metrics) as [metric, data]}
                                                    <div class="bg-gray-50 p-4 rounded-lg">
                                                        <h4 class="font-medium text-gray-900 capitalize">{metric.replace('_', ' ')}</h4>
                                                        <dl class="mt-2 space-y-1">
                                                            <div class="flex justify-between text-sm">
                                                                <dt class="text-gray-500">Average:</dt>
                                                                <dd class="text-gray-900">{data.average?.toFixed(2) || 'N/A'}</dd>
                                                            </div>
                                                            <div class="flex justify-between text-sm">
                                                                <dt class="text-gray-500">Total:</dt>
                                                                <dd class="text-gray-900">{data.total?.toFixed(0) || 'N/A'}</dd>
                                                            </div>
                                                            <div class="flex justify-between text-sm">
                                                                <dt class="text-gray-500">Count:</dt>
                                                                <dd class="text-gray-900">{data.count || 'N/A'}</dd>
                                                            </div>
                                                        </dl>
                                                    </div>
                                                {/each}
                                            </div>
                                        </div>
                                    {/if}
                                {:else}
                                    <div class="text-center py-12">
                                        <Icon icon="mdi:chart-line" class="w-12 h-12 mx-auto text-gray-300 mb-4" />
                                        <p class="text-gray-500">No analytics data available</p>
                                    </div>
                                {/if}
                            </div>
                        
                        {:else if $activeTab === 'deployments'}
                            <!-- Deployments Tab -->
                            <div class="space-y-6">
                                <div class="flex justify-between items-center">
                                    <h3 class="text-lg font-medium text-gray-900">Deployment Status</h3>
                                    <button
                                        on:click={() => showDeployModal = true}
                                        class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
                                    >
                                        <Icon icon="mdi:rocket" class="w-4 h-4" />
                                        <span>Deploy</span>
                                    </button>
                                </div>
                                
                                {#if $deployments.length > 0}
                                    <div class="grid gap-4">
                                        {#each $deployments as deployment}
                                            <div class="border rounded-lg p-4">
                                                <div class="flex items-center justify-between">
                                                    <div>
                                                        <h4 class="font-medium text-gray-900 capitalize">
                                                            {deployment.environment?.replace('_', ' ') || 'Unknown Environment'}
                                                        </h4>
                                                        <p class="text-sm text-gray-500">Version: {deployment.version || 'N/A'}</p>
                                                    </div>
                                                    <span class="px-2 py-1 text-xs rounded-full {
                                                        deployment.deployment_status === 'active' ? 'bg-green-100 text-green-800' :
                                                        deployment.deployment_status === 'failed' ? 'bg-red-100 text-red-800' :
                                                        'bg-yellow-100 text-yellow-800'
                                                    }">
                                                        {deployment.deployment_status || deployment.status || 'Unknown'}
                                                    </span>
                                                </div>
                                                
                                                <div class="mt-3 grid grid-cols-3 gap-4 text-sm">
                                                    <div>
                                                        <span class="text-gray-500">Conversations:</span>
                                                        <span class="text-gray-900 ml-1">{deployment.total_conversations || 0}</span>
                                                    </div>
                                                    <div>
                                                        <span class="text-gray-500">Avg Response:</span>
                                                        <span class="text-gray-900 ml-1">{deployment.avg_response_time?.toFixed(1) || 'N/A'}s</span>
                                                    </div>
                                                    <div>
                                                        <span class="text-gray-500">Rating:</span>
                                                        <span class="text-gray-900 ml-1">{deployment.user_satisfaction_rating?.toFixed(1) || 'N/A'}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        {/each}
                                    </div>
                                {:else}
                                    <div class="text-center py-12">
                                        <Icon icon="mdi:rocket-outline" class="w-12 h-12 mx-auto text-gray-300 mb-4" />
                                        <p class="text-gray-500">No deployments found</p>
                                        <button
                                            on:click={() => showDeployModal = true}
                                            class="text-blue-600 hover:underline mt-2"
                                        >
                                            Deploy this assistant
                                        </button>
                                    </div>
                                {/if}
                            </div>
                        
                        {:else if $activeTab === 'conversations'}
                            <!-- Conversations Tab -->
                            <div class="space-y-6">
                                <div class="flex justify-between items-center">
                                    <h3 class="text-lg font-medium text-gray-900">Active Conversations</h3>
                                    <button
                                        on:click={() => startConversation($selectedAssistant.id)}
                                        class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center space-x-2"
                                    >
                                        <Icon icon="mdi:chat-plus" class="w-4 h-4" />
                                        <span>Start Conversation</span>
                                    </button>
                                </div>
                                
                                {#if $conversations.length > 0}
                                    <div class="grid gap-4">
                                        {#each $conversations as conversation}
                                            <div class="border rounded-lg p-4">
                                                <div class="flex items-center justify-between">
                                                    <div>
                                                        <h4 class="font-medium text-gray-900">Session {conversation.session_id.slice(-8)}</h4>
                                                        <p class="text-sm text-gray-500">
                                                            Started: {formatDate(conversation.started_at)}
                                                        </p>
                                                    </div>
                                                    <div class="text-right">
                                                        <div class="text-sm text-gray-900">{conversation.interaction_count} interactions</div>
                                                        <div class="text-xs text-gray-500">
                                                            Avg: {conversation.avg_response_time?.toFixed(1) || 'N/A'}s
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        {/each}
                                    </div>
                                {:else}
                                    <div class="text-center py-12">
                                        <Icon icon="mdi:chat-outline" class="w-12 h-12 mx-auto text-gray-300 mb-4" />
                                        <p class="text-gray-500">No active conversations</p>
                                        <button
                                            on:click={() => startConversation($selectedAssistant.id)}
                                            class="text-blue-600 hover:underline mt-2"
                                        >
                                            Start a conversation
                                        </button>
                                    </div>
                                {/if}
                            </div>
                        
                        {:else if $activeTab === 'prompts'}
                            <!-- Prompts Tab -->
                            <div class="space-y-6">
                                <div class="flex justify-between items-center">
                                    <h3 class="text-lg font-medium text-gray-900">Linked Prompts</h3>
                                    <button class="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 flex items-center space-x-2">
                                        <Icon icon="mdi:link-plus" class="w-4 h-4" />
                                        <span>Link Prompt</span>
                                    </button>
                                </div>
                                
                                {#if $prompts.length > 0}
                                    <div class="grid gap-4">
                                        {#each $prompts as prompt}
                                            <div class="border rounded-lg p-4">
                                                <div class="flex items-start justify-between">
                                                    <div>
                                                        <h4 class="font-medium text-gray-900">{prompt.prompt?.title || 'Untitled Prompt'}</h4>
                                                        <p class="text-sm text-gray-500 mt-1">{prompt.prompt?.description || 'No description'}</p>
                                                        <div class="flex items-center space-x-4 mt-2">
                                                            <span class="px-2 py-1 text-xs rounded-full {
                                                                prompt.mapping_type === 'primary' ? 'bg-blue-100 text-blue-800' :
                                                                prompt.mapping_type === 'fallback' ? 'bg-yellow-100 text-yellow-800' :
                                                                'bg-gray-100 text-gray-800'
                                                            }">
                                                                {prompt.mapping_type}
                                                            </span>
                                                            {#if prompt.version}
                                                                <span class="text-xs text-gray-500">
                                                                    v{prompt.version.number} - {prompt.version.title}
                                                                </span>
                                                            {/if}
                                                            {#if prompt.category}
                                                                <span class="px-2 py-1 text-xs rounded-full" style="background-color: {prompt.category.color}20; color: {prompt.category.color};">
                                                                    {prompt.category.name}
                                                                </span>
                                                            {/if}
                                                        </div>
                                                    </div>
                                                    <button class="text-gray-400 hover:text-red-600">
                                                        <Icon icon="mdi:unlink" class="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </div>
                                        {/each}
                                    </div>
                                {:else}
                                    <div class="text-center py-12">
                                        <Icon icon="mdi:file-document-outline" class="w-12 h-12 mx-auto text-gray-300 mb-4" />
                                        <p class="text-gray-500">No prompts linked</p>
                                        <button class="text-blue-600 hover:underline mt-2">
                                            Link a prompt
                                        </button>
                                    </div>
                                {/if}
                            </div>
                        {/if}
                    </div>
                </div>
            {:else}
                <div class="bg-white rounded-lg shadow-sm border p-12 text-center">
                    <Icon icon="mdi:robot-outline" class="w-16 h-16 mx-auto text-gray-300 mb-4" />
                    <h3 class="text-lg font-medium text-gray-900 mb-2">Select an Assistant</h3>
                    <p class="text-gray-500">Choose an assistant from the list to view details and manage its configuration.</p>
                </div>
            {/if}
        </div>
    </div>
</div>

<!-- Modals -->

<!-- Create Assistant Modal -->
{#if showCreateModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-xl font-bold text-gray-900">Create New Assistant</h2>
                <button on:click={() => showCreateModal = false}>
                    <Icon icon="mdi:close" class="w-6 h-6 text-gray-400" />
                </button>
            </div>
            
            <form on:submit|preventDefault={createAssistant} class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                    <input
                        type="text"
                        bind:value={newAssistant.name}
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Enter assistant name"
                    >
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea
                        bind:value={newAssistant.description}
                        rows="3"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Describe what this assistant does"
                    ></textarea>
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
                        <select
                            bind:value={newAssistant.assistant_type}
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            {#each assistantTypes as type}
                                <option value={type.value}>{type.name}</option>
                            {/each}
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Model</label>
                        <select
                            bind:value={newAssistant.model_id}
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="gpt-4">GPT-4</option>
                            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                            <option value="claude-3-opus">Claude 3 Opus</option>
                            <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                        </select>
                    </div>
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
                        <input
                            type="number"
                            bind:value={newAssistant.temperature}
                            min="0"
                            max="2"
                            step="0.1"
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Max Tokens</label>
                        <input
                            type="number"
                            bind:value={newAssistant.max_tokens}
                            min="1"
                            max="8000"
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                    </div>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">System Prompt *</label>
                    <textarea
                        bind:value={newAssistant.system_prompt}
                        required
                        rows="6"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Enter the system prompt that defines the assistant's behavior and personality"
                    ></textarea>
                </div>
                
                <div class="flex justify-end space-x-4 pt-4">
                    <button
                        type="button"
                        on:click={() => showCreateModal = false}
                        class="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={$loading}
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
                    >
                        {#if $loading}
                            <Icon icon="mdi:loading" class="w-4 h-4 animate-spin" />
                        {/if}
                        <span>Create Assistant</span>
                    </button>
                </div>
            </form>
        </div>
    </div>
{/if}

<!-- Deploy Modal -->
{#if showDeployModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg p-6 w-full max-w-lg">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-xl font-bold text-gray-900">Deploy Assistant</h2>
                <button on:click={() => showDeployModal = false}>
                    <Icon icon="mdi:close" class="w-6 h-6 text-gray-400" />
                </button>
            </div>
            
            <form on:submit|preventDefault={() => deployAssistant($selectedAssistant.id)} class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Environment</label>
                    <select
                        bind:value={deploymentForm.environment}
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        {#each deploymentEnvironments as env}
                            <option value={env.value}>{env.name} - {env.description}</option>
                        {/each}
                    </select>
                </div>
                
                <div class="flex justify-end space-x-4 pt-4">
                    <button
                        type="button"
                        on:click={() => showDeployModal = false}
                        class="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={$loading}
                        class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center space-x-2"
                    >
                        {#if $loading}
                            <Icon icon="mdi:loading" class="w-4 h-4 animate-spin" />
                        {/if}
                        <span>Deploy</span>
                    </button>
                </div>
            </form>
        </div>
    </div>
{/if}

<!-- Delete Confirmation Modal -->
{#if showDeleteModal && assistantToDelete}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg p-6 w-full max-w-md">
            <div class="flex items-center mb-4">
                <div class="bg-red-100 p-3 rounded-full mr-4">
                    <Icon icon="mdi:alert" class="w-6 h-6 text-red-600" />
                </div>
                <div>
                    <h2 class="text-lg font-bold text-gray-900">Delete Assistant</h2>
                    <p class="text-gray-600">This action cannot be undone</p>
                </div>
            </div>
            
            <p class="text-gray-700 mb-6">
                Are you sure you want to delete "<strong>{assistantToDelete.name}</strong>"? 
                This will permanently remove the assistant and all its configuration.
            </p>
            
            <div class="flex justify-end space-x-4">
                <button
                    on:click={() => { showDeleteModal = false; assistantToDelete = null; }}
                    class="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300"
                >
                    Cancel
                </button>
                <button
                    on:click={() => deleteAssistant(assistantToDelete.id)}
                    disabled={$loading}
                    class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center space-x-2"
                >
                    {#if $loading}
                        <Icon icon="mdi:loading" class="w-4 h-4 animate-spin" />
                    {/if}
                    <span>Delete</span>
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    .line-clamp-2 {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>