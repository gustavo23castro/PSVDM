// Source: https://github.com/greensoftwarelab/Energy-Languages
//   tree/master/CSharp/fannkuch-redux
// contributed by Isaac Gouy, transliterated from Oleg Mazurov's Java program
// concurrency fix and minor improvements by Peperud
// Adapted for BenchmarkDotNet: removed static state, removed Main(),
// exposed Compute(int n) API. Threading model unchanged.

using System;
using System.Threading;
using System.Threading.Tasks;

namespace FannkuchBenchmark;

public static class FannkuchCore
{
    const int NCHUNKS = 150;
    const int INT_SIZE = 4;

    // Holds all per-invocation mutable state that was static in the original.
    // Shared by all Worker instances within one Compute() call.
    private sealed class RunCtx
    {
        public int CHUNKSZ;
        public int NTASKS;
        public int n;
        public int[] Fact = null!;
        public int[] maxFlips = null!;
        public int[] chkSums = null!;
        public int taskId;
    }

    // Mirrors the original FannkuchRedux instance class.
    // p, pp, count are per-worker; all other state lives in RunCtx.
    private sealed class Worker
    {
        readonly RunCtx ctx;
        int[] p = null!, pp = null!, count = null!;

        public Worker(RunCtx ctx) { this.ctx = ctx; }

        void FirstPermutation(int idx)
        {
            for (int i = 0; i < p.Length; ++i)
            {
                p[i] = i;
            }

            for (int i = count.Length - 1; i > 0; --i)
            {
                int d = idx / ctx.Fact[i];
                count[i] = d;
                idx = idx % ctx.Fact[i];

                Buffer.BlockCopy(p, 0, pp, 0, (i + 1) * INT_SIZE);

                for (int j = 0; j <= i; ++j)
                {
                    p[j] = j + d <= i ? pp[j + d] : pp[j + d - i - 1];
                }
            }
        }

        bool NextPermutation()
        {
            int first = p[1];
            p[1] = p[0];
            p[0] = first;

            int i = 1;
            while (++count[i] > i)
            {
                count[i++] = 0;
                int next = p[0] = p[1];
                for (int j = 1; j < i; ++j)
                {
                    p[j] = p[j + 1];
                }
                p[i] = first;
                first = next;
            }
            return true;
        }

        int CountFlips()
        {
            int flips = 1;
            int first = p[0];
            if (p[first] != 0)
            {
                Buffer.BlockCopy(p, 0, pp, 0, pp.Length * INT_SIZE);
                do
                {
                    ++flips;
                    for (int lo = 1, hi = first - 1; lo < hi; ++lo, --hi)
                    {
                        int t = pp[lo];
                        pp[lo] = pp[hi];
                        pp[hi] = t;
                    }
                    int tp = pp[first];
                    pp[first] = first;
                    first = tp;
                } while (pp[first] != 0);
            }
            return flips;
        }

        void RunTask(int task)
        {
            int idxMin = task * ctx.CHUNKSZ;
            int idxMax = Math.Min(ctx.Fact[ctx.n], idxMin + ctx.CHUNKSZ);

            FirstPermutation(idxMin);

            int maxflips = 1;
            int chksum = 0;
            for (int i = idxMin; ;)
            {
                if (p[0] != 0)
                {
                    int flips = CountFlips();

                    if (maxflips < flips) maxflips = flips;

                    chksum += i % 2 == 0 ? flips : -flips;
                }

                if (++i == idxMax)
                {
                    break;
                }

                NextPermutation();
            }
            ctx.maxFlips[task] = maxflips;
            ctx.chkSums[task] = chksum;
        }

        public void Run()
        {
            p = new int[ctx.n];
            pp = new int[ctx.n];
            count = new int[ctx.n];

            int task;
            while ((task = Interlocked.Increment(ref ctx.taskId)) < ctx.NTASKS)
            {
                RunTask(task);
            }
        }
    }

    public static (int checksum, int maxFlips) Compute(int n)
    {
        var nLen = n + 1;

        var Fact = new int[nLen];
        Fact[0] = 1;
        for (int i = 1; i < nLen; ++i)
        {
            Fact[i] = Fact[i - 1] * i;
        }

        int CHUNKSZ = (Fact[n] + NCHUNKS - 1) / NCHUNKS;
        int NTASKS = (Fact[n] + CHUNKSZ - 1) / CHUNKSZ;

        var ctx = new RunCtx
        {
            n = n,
            Fact = Fact,
            CHUNKSZ = CHUNKSZ,
            NTASKS = NTASKS,
            maxFlips = new int[NTASKS],
            chkSums = new int[NTASKS],
            taskId = -1,
        };

        int nthreads = Environment.ProcessorCount + 1;

        Task[] tasks = new Task[nthreads];
        for (int i = 0; i < nthreads; ++i)
        {
            tasks[i] = Task.Run(() =>
            {
                new Worker(ctx).Run();
            });
        }
        Task.WaitAll(tasks);

        int res = 0, chk = 0;

        Task[] t2 =
        {
            Task.Run(() =>
            {
                for (int v = 0; v < ctx.NTASKS; v++)
                {
                    chk += ctx.chkSums[v];
                }
            }),

            Task.Run(() =>
            {
                for (int v = 0; v < ctx.NTASKS; v++)
                {
                    if (res < ctx.maxFlips[v]) res = ctx.maxFlips[v];
                }
            })
        };

        Task.WaitAll(t2);

        return (chk, res);
    }
}
