
def parallel_unifrac(ctx, table, phylogeny, weighted):
    pass

@plugin.Pipeline('Core Metrics', description='Do a bunch of stuff yo.')
@Action.input('table', FeatureTable[Frequency], description='A description for this input')
@Action.parameter('counts_per_sample', Int)
@Action.output('faith_alpha', Alpha)
def core_metrics(ctx, table, phylogeny, counts_per_sample):
    rarefied_table, = ctx.schedule('q2_feature_table', 'rarefy',
                                   table=table, counts_per_sample=counts_per_sample)

    yield ctx.schedule(
        'q2_diversity', 'alpha_phylogenetic', table=rarefied_table,
        phylogeny=phylogeny, metric='faith_pd').alpha_diversity

    for metric in 'observed_otus', 'shannon', 'pielou_e':
        yield ctx.schedule('q2_diversity', 'alpha', table=rarefied_table,
                           metric=metric).alpha_diversity

    if ctx.pool_size < 10:
        ctx.wait_until_free('parallel_unifrac')
    elif:
        ctx.wait_until_free('parallel_unifrac', 0.9)

    unweighted_unifrac_distance_matrix, = \
        ctx.schedule('q2_diversity', 'parallel_unifrac',
                     table=rarefied_table, phylogeny=phylogeny,
                     weighted=False)
    yield unweighted_unifrac_distance_matrix

    ctx.wait()

    weighted_unifrac_distance_matrix, = \
        ctx.schedule('q2_diversity', 'parallel_unifrac',
                     table=rarefied_table, phylogeny=phylogeny,
                     weighted=False)
    yield weighted_unifrac_distance_matrix

    jaccard_distance_matrix, = \
        ctx.schedule('q2_diversity', 'beta', table=rarefied_table,
                     metric='jaccard')
    yield jaccard_distance_matrix


    bray_curtis_distance_matrix, = ctx.schedule('q2_diversity', 'beta',
                                                table=rarefied_table,
                                                metric='braycurtis')

    r = bray_curtis_distance_matrix.collect()
    if r.view(SomeParticularWay) == some_condition:
        do_one_thing
    else:
        pass


    yield bray_curtis_distance_matrix

    for matrix in (unweighted_unifrac_distance_matrix,
                   weighted_unifrac_distance_matrix,
                   jaccard_distance_matrix,
                   bray_curtis_distance_matrix):
        yield ctx.schedule('q2_diversity', 'pcoa', distance_matrix=matrix)



def alpha_rarefaction(ctx, feature_table, iterations, max_depth):

    ctx.repeat_schedule(100, 'foo', 'bar', feature_table, depth)





ctx.schedule('q2_diversity', 'core_metrics', a, b, 100)




# Instances, not functions
action = some_plugin.actions.core_metrics()
r = action(a, b)

action = some_plugin.actions.core_metrics(ctx)
r = action(a, b)

action = some_plugin.actions.core_metrics(ctx, parallel_unifrac=ctx2)
r = action(a, b)

action = some_plugin.actions.core_metrics(parallel_unifrac=ctx2)
r = action(a, b)


# Function Instances, explicitely curried (identical to above):
r = some_plugin.actions.core_metrics()(a, b)

r = some_plugin.actions.core_metrics(ctx)(a, b)

r = some_plugin.actions.core_metrics(ctx, parallel_unifrac=ctx2)(a, b)

r = some_plugin.actions.core_metrics(parallel_unifrac=ctx2)(a, b)


# Functions, but implicitly curried:
r = some_plugin.actions.core_metrics(a, b)

r = some_plugin.actions.core_metrics(ctx)(a, b)

r = some_plugin.actions.core_metrics(ctx, parallel_unifrac=ctx2)(a, b)

r = some_plugin.actions.core_metrics(parallel_unifrac=ctx2)(a, b)


# Functions, but explicitly curried with nonstandard syntax:
r = some_plugin.actions.core_metrics(a, b)

r = some_plugin.actions.core_metrics[ctx](a, b)

r = some_plugin.actions.core_metrics[ctx, 'parallel_unifrac':ctx2](a, b)

r = some_plugin.actions.core_metrics['parallel_unifrac':ctx2](a, b)

# So... this is really easy to implement:
typical_case = some_plugin.actions.core_metrics[my_ctx]
context_inheritence = typical_case['parallel_unifrac':ctx2]

r = typical_case(a, b)
r = context_inheritence(a, b)


results = q2_diversity.actions.core_metrics(a, b)


ctx = execution_context()
if (other_context):
    ctx = other_context

with ctx:
    do_thing()


with execution_context(config, classify=high_mem_config):
    results = q2_diversity.actions.pipeline_magic(a, b)

try:
    results.wait()
except PipelineFailure:
    with execution_context()(results):
        better_results = q2_diversity.actions.pipeline_magic(a, b)


# Quick and dirty pipeline
@qiime.pipeline
def my_custom_pipeline(ctx, a, b, c):
    r = ctx.schedule('some_plugin', 'some_method', a, b, c)
    yield r.x

    r = ctx.schedule('some_plugin', 'other_method', b)
    yield from r


with execution_context(None, artifacts, overrride_action_name=other_config):
    results = my_custom_pipeline(a, b, c)



# Alternative

with execution_context() as ctx:
    plan = ctx.schedule('some_plugin', 'some_method', a, b, c)
    future_artifact = ctx.collect_artifact(plan.foo)
    future_artifact.wait()


results['alpha_diversity']
results[0]

# blocks until all results are complete, will raise PipelineFailure for any failure, returns self
results.wait()

# one of {'waiting', 'running', 'failed', 'completed'}
results.status

# returns destructor, runs callback(results) when state changes
results.on([status], callback)

# blocks until specific result is complete, will raise PipelineFailure for relevent failure
results[str | int]

# returns virtual artifact (promise?)
results.promised[str | int]

# blocks in each iteration until that iterations result is ready, will raise PipelineFailure relevent to iteration
iter(results)

# number of defined results
len(results)

# set of keys which are completed
results.completed_keys
results.completed_idx

# set of keys which are pending
results.pending_keys
results.pending_idx

# set of keys which failed
results.failed_keys
results.failed_idx


plannedResult.wait() => result


some_method.call(a, b)




some_method.async(a, b)
some_method(a, b)

with execution_context():
    results = some_method(a, b)
    pipeline_results = some_pipeline.async(a, b)

results = some_method(a, b)

with execution_context() as ctx:
    try:
      results = some_method(a, b, ctx=ctx)
    except Exception:
        new_ctx = get_context()

        results = some_method(a, b, ctx=new_ctx)
    async_result = some_method.async(a,b,ctx=ctx)


future_result = some_method(a, b)

foo = future_result['foo']
#pipeline_results = some_pipeline.async(a, b)


def a_pipeline(ctx, a, b):
    plan = ctx.schedule('foo', 'bar', a)
    x = plan['result_x']
    yield x

    yield from ctx.schedule('foo', 'bar', a)

    intermediate = x
    if x.collect().view(Something).is_something():
        intermediate = ctx.schedule('foo', 'bar', intermediate)['value']

    param = 0
    if intermediate in SomeType[Foo] % Properties('alpha'):
        param = 1

    yield from ctx.schedule('foo', 'bar', b, intermediate, param=param)


Partial[SemanticType]

class ArgumentCollection:
    pass


class ExecutionContext:
    def schedule(self, plugin_name, action_name, *args, **kwargs) -> Plan:
        results = signature(*args, **kwargs)

    def wait(self, queue=None) -> None:
        pass

    def collect_result(self, planned_result):
        pass


class Plan:
    def __iter__(self) -> Iterator[PlannedResult]:
        pass

    def __getitem__(self, idx) -> PlannedResult:
        pass

    def checkpoint(self):
        pass


class PlannedResult:
    @property
    def type(self):
        pass

    def collect(self) -> Artifact | Visualization:
        return self._ctx.collect_result(self)




def overspecific_pipeline(ctx, a, b):
    with ctx.connect_joblib():
        anything_with_joblib_here()

def another(ctx, a, b):
    with ctx.distributed_client() as client:
        client.submit("things")
